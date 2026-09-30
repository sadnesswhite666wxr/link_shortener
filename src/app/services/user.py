from typing import Annotated

from fastapi import Depends, HTTPException
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select
from starlette import status

from src.app.database.session import DBSession
from src.app.models import User
from src.app.models.schemas.user import UserCreate, UserRead, UserUpdate, UserWithRoles
from src.app.services.redis import RedisService, RedisServiceDep

password_hash = PasswordHash.recommended()


class UserService:
    def __init__(self, session: AsyncSession, redis_service: RedisService) -> None:
        self.session = session
        self.redis = redis_service

    async def get_user_with_roles(self, user_id: int) -> UserWithRoles:
        user_query = select(User).where(User.id == user_id).options(selectinload(User.roles))
        result = await self.session.scalar(user_query)
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return UserWithRoles.model_validate(result)

    async def get_all_users(self) -> list[UserRead]:
        user_query = select(User)
        result = await self.session.scalars(user_query)
        db_users = result.all()

        return [UserRead.model_validate(record) for record in db_users]

    async def create_user(self, user: UserCreate) -> UserRead:
        user_query = select(User).where(User.username == user.username)
        result = await self.session.execute(user_query)
        record = result.scalar_one_or_none()
        if record is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

        user_data = user.model_dump(exclude_unset=True)
        if "password" in user_data:
            user_data["hashed_password"] = password_hash.hash(user_data["password"])
            user_data.pop("password")

        db_user = User.model_validate(user_data)

        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)

        return UserRead.model_validate(db_user)

    async def update_user(self, user_id: int, updated_user: UserUpdate) -> UserRead:
        user_query = select(User).where(User.id == user_id)
        result = await self.session.execute(user_query)
        user_db = result.scalar_one_or_none()
        if user_db is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        old_username = user_db.username
        user_data = updated_user.model_dump(exclude_unset=True)
        if "password" in user_data:
            user_data["hashed_password"] = password_hash.hash(user_data["password"])
            user_data.pop("password")

        user_db.sqlmodel_update(user_data)
        await self.session.commit()
        await self.session.refresh(user_db)

        await self.redis.delete_user_object(old_username)

        return UserRead.model_validate(user_db)

    async def delete_user(self, user_id: int) -> None:
        user_query = select(User).where(User.id == user_id)
        result = await self.session.execute(user_query)
        db_user = result.scalar_one_or_none()
        if db_user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        await self.session.delete(db_user)
        await self.session.commit()

        await self.redis.delete_user_object(db_user.username)


def get_user_service(session: DBSession, redis_service: RedisServiceDep) -> UserService:
    return UserService(session=session, redis_service=redis_service)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
