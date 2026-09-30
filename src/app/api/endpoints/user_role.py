from typing import Annotated

from fastapi import APIRouter, Security
from starlette import status

from src.app.api.data.permission_enum import PermissionEnum
from src.app.api.endpoints.auth import get_current_user
from src.app.models import User
from src.app.models.schemas.user import (
    UserAddRole,
    UserRedis,
    UserRemoveRole,
    UserWithRoles,
)
from src.app.services.user_role import UserRoleServiceDep

user_role_router = APIRouter(
    prefix="/user_role",
    tags=["USER_ROLE"],
)


@user_role_router.post("/{user_id}", status_code=status.HTTP_201_CREATED)
async def add_role_to_user(
    _user: Annotated[User | UserRedis, Security(get_current_user, scopes=[PermissionEnum.USER_ROLE_CREATE])],
    user_id: int,
    user_roles: UserAddRole,
    user_role_service: UserRoleServiceDep,
) -> UserWithRoles:
    return await user_role_service.add_user_role(user_id, user_roles)


@user_role_router.post("/{user_id}/revoke", status_code=status.HTTP_200_OK)
async def remove_role_from_user(
    _user: Annotated[User | UserRedis, Security(get_current_user, scopes=[PermissionEnum.USER_ROLE_DELETE])],
    user_id: int,
    deleted_roles: UserRemoveRole,
    user_role_service: UserRoleServiceDep,
) -> UserWithRoles:
    return await user_role_service.remove_role_from_user(user_id, deleted_roles)
