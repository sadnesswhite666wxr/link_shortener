from typing import Annotated

from fastapi import APIRouter, Security
from starlette import status
from starlette.responses import Response

from src.app.api.data.permission_enum import PermissionEnum
from src.app.api.endpoints.auth import get_current_user
from src.app.models.schemas.user import (
    UserCreate,
    UserRead,
    UserRedis,
    UserUpdate,
    UserWithRoles,
)
from src.app.models.tables.user import User
from src.app.services.user import UserServiceDep

user_router = APIRouter(
    prefix="/users",
    tags=["USERS"],
)


@user_router.get("/list", status_code=status.HTTP_200_OK)
async def get_all_users(
    _user: Annotated[User | UserRedis, Security(get_current_user, scopes=[PermissionEnum.USER_READ])],
    user_service: UserServiceDep,
) -> list[UserRead]:
    return await user_service.get_all_users()


@user_router.get("/{user_id}", status_code=status.HTTP_200_OK)
async def get_user_with_roles(
    _user: Annotated[User | UserRedis, Security(get_current_user, scopes=[PermissionEnum.USER_READ])],
    user_id: int,
    user_service: UserServiceDep,
) -> UserWithRoles:
    return await user_service.get_user_with_roles(user_id)


@user_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    _user: Annotated[User | UserRedis, Security(get_current_user, scopes=[PermissionEnum.USER_CREATE])],
    new_user: UserCreate,
    user_service: UserServiceDep,
) -> UserRead:
    return await user_service.create_user(new_user)


@user_router.put("/{user_id}", status_code=status.HTTP_200_OK)
async def update_user(
    _user: Annotated[User | UserRedis, Security(get_current_user, scopes=[PermissionEnum.USER_UPDATE])],
    user_id: int,
    updated_user_data: UserUpdate,
    user_service: UserServiceDep,
) -> UserRead:
    return await user_service.update_user(user_id, updated_user_data)


@user_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    _user: Annotated[User | UserRedis, Security(get_current_user, scopes=[PermissionEnum.USER_DELETE])],
    user_id: int,
    user_service: UserServiceDep,
) -> Response:
    await user_service.delete_user(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
