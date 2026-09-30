from typing import Annotated

from fastapi import APIRouter, Security
from starlette import status
from starlette.responses import Response

from src.app.api.data.permission_enum import PermissionEnum
from src.app.api.endpoints.auth import get_current_user
from src.app.models import User
from src.app.models.schemas.role import (
    RoleCreate,
    RoleRead,
    RoleUpdate,
    RoleWithPermission,
)
from src.app.models.schemas.user import UserRedis
from src.app.services.role import RoleServiceDep

roles_router = APIRouter(
    prefix="/roles",
    tags=["ROLES"],
)


@roles_router.get("/list", status_code=status.HTTP_200_OK)
async def get_all_roles(
    _user: Annotated[User | UserRedis, Security(get_current_user, scopes=[PermissionEnum.ROLE_READ])],
    role_service: RoleServiceDep,
) -> list[RoleRead]:
    return await role_service.get_all_roles()


@roles_router.get("/{role_id}", status_code=status.HTTP_200_OK)
async def get_role_with_permissions(
    _user: Annotated[User | UserRedis, Security(get_current_user, scopes=[PermissionEnum.ROLE_READ])],
    role_id: int,
    role_service: RoleServiceDep,
) -> RoleWithPermission:
    return await role_service.get_role_with_permission(role_id)


@roles_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_role_with_permission(
    role: RoleCreate,
    _user: Annotated[User | UserRedis, Security(get_current_user, scopes=[PermissionEnum.ROLE_CREATE])],
    role_service: RoleServiceDep,
) -> RoleWithPermission:
    return await role_service.create_role(role)


@roles_router.put("/update/{role_id}", status_code=status.HTTP_200_OK)
async def update_role_with_permission(
    _user: Annotated[User | UserRedis, Security(get_current_user, scopes=[PermissionEnum.ROLE_UPDATE])],
    updated_role: RoleUpdate,
    role_id: int,
    role_service: RoleServiceDep,
) -> RoleWithPermission:
    return await role_service.update_role(role_id, updated_role)


@roles_router.delete("/delete/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    _user: Annotated[User | UserRedis, Security(get_current_user, scopes=[PermissionEnum.ROLE_DELETE])],
    role_id: int,
    role_service: RoleServiceDep,
) -> Response:
    await role_service.delete_role(role_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
