from typing import Annotated

from fastapi import APIRouter, Security

from src.app.api.data.permission_enum import PermissionEnum
from src.app.api.endpoints.auth import get_current_user
from src.app.models import User
from src.app.models.schemas.permission import PermissionRead
from src.app.models.schemas.user import UserRedis
from src.app.services.permissions import PermissionServiceDep

permissions_router = APIRouter(
    prefix="/permissions",
    tags=["PERMISSIONS"],
)


@permissions_router.get("/")
async def get_all_permissions(
    _user: Annotated[User | UserRedis, Security(get_current_user, scopes=[PermissionEnum.PERMISSION_READ])],
    permission_service: PermissionServiceDep,
) -> list[PermissionRead]:
    return await permission_service.get_all_permissions()
