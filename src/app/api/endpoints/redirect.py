from typing import Annotated

from fastapi import APIRouter, Security
from starlette import status
from starlette.responses import RedirectResponse

from src.app.api.data.permission_enum import PermissionEnum
from src.app.api.endpoints.auth import get_current_user
from src.app.models import User
from src.app.models.schemas.user import UserRedis
from src.app.services.redirect import RedirectServiceDep

redirect_router = APIRouter(
    tags=["redirect"],
)


@redirect_router.get("/{link_data_shorten}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def redirect_to_link(
    link_data_shorten: str,
    user: Annotated[
        User | UserRedis,
        Security(get_current_user, scopes=[PermissionEnum.LINK_DATA_READ_ALL, PermissionEnum.LINK_DATA_READ_OWN]),
    ],
    redirect_service: RedirectServiceDep,
) -> RedirectResponse:
    origin = await redirect_service.redirect(link_data_shorten=link_data_shorten, user=user)
    return RedirectResponse(origin, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
