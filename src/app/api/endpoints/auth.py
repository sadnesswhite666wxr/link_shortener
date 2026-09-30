from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
import structlog
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select
from starlette import status

from src.app.config.settings import get_settings
from src.app.database.session import DBSession
from src.app.models import Role
from src.app.models.schemas.access_token import AccessToken
from src.app.models.schemas.user import UserRedis
from src.app.models.tables.user import User
from src.app.services.redis import RedisServiceDep
from src.app.utils.user_scopes import extract_scopes_from_user

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False,
)

password_hash = PasswordHash.recommended()

DUMMY_HASH = password_hash.hash("theworstpassever")

auth_router = APIRouter(prefix="/auth", tags=["AUTH"])

settings = get_settings()

logger = structlog.get_logger()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


async def get_user(username: str, db_session: AsyncSession) -> User | None:
    user = await db_session.execute(
        select(User).where(User.username == username).options(selectinload(User.roles).selectinload(Role.permissions))
    )

    user = user.scalar_one_or_none()

    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_MIN)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        payload=to_encode,
        key=settings.APP_KEY,
        algorithm=settings.ALGORITHM,
    )

    return encoded_jwt


async def authenticate_user(db_session: AsyncSession, username: str, password: str) -> User | None:
    user = await db_session.execute(select(User).where(User.username == username))
    user = user.scalar_one_or_none()
    if not user:
        verify_password(password, DUMMY_HASH)
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


async def get_current_user(
    db_session: DBSession,
    redis_service: RedisServiceDep,
    security_scopes: SecurityScopes,
    token: Annotated[str | None, Depends(oauth2_scheme)] = None,
) -> User | UserRedis:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(jwt=token, key=settings.APP_KEY, algorithms=settings.ALGORITHM)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

    except InvalidTokenError:
        raise credentials_exception

    user = await redis_service.get_user_object(username)

    if user is None:
        user = await get_user(username=username, db_session=db_session)
        if not user:
            raise credentials_exception

        await redis_service.set_user_object(user)

    user_scopes = extract_scopes_from_user(user)

    if security_scopes.scopes and not any(scope in user_scopes for scope in security_scopes.scopes):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


@auth_router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db_session: DBSession,
) -> AccessToken:
    user: User = await authenticate_user(
        db_session=db_session,
        username=form_data.username,
        password=form_data.password,
    )
    if user is None:
        await logger.awarning(
            "failed_login_attempt", attempted_username=form_data.username, reason="invalid_credentials"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_MIN)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires,
    )

    return AccessToken(access_token=access_token, token_type="bearer")
