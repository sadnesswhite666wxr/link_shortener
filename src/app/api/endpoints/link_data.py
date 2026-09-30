from typing import Annotated

from fastapi import APIRouter, Security
from starlette import status
from starlette.responses import Response

from src.app.api.data.permission_enum import PermissionEnum
from src.app.api.endpoints.auth import get_current_user
from src.app.models import User
from src.app.models.schemas.link_data import (
    LinkDataCreate,
    LinkDataRead,
    LinkDataUpdate,
)
from src.app.models.schemas.user import UserRedis
from src.app.services.link_data import (
    LinkDataServiceDep,
)

link_data_router = APIRouter(
    prefix="/shortener",
    tags=["SHORTENER"],
)


@link_data_router.get("/", status_code=status.HTTP_200_OK)
async def get_all_shorten_urls(
    user: Annotated[
        User | UserRedis,
        Security(get_current_user, scopes=[PermissionEnum.LINK_DATA_READ_ALL, PermissionEnum.LINK_DATA_READ_OWN]),
    ],
    link_data_service: LinkDataServiceDep,
) -> list[LinkDataRead]:
    return await link_data_service.get_all_visible_records(user)


@link_data_router.get("/{link_data_id}", status_code=status.HTTP_200_OK)
async def get_shorten_url(
    link_data_id: int,
    user: Annotated[
        User | UserRedis,
        Security(get_current_user, scopes=[PermissionEnum.LINK_DATA_READ_ALL, PermissionEnum.LINK_DATA_READ_OWN]),
    ],
    link_data_service: LinkDataServiceDep,
) -> LinkDataRead:
    return await link_data_service.get_record_by_id(link_data_id=link_data_id, user=user)


@link_data_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_shorten_url(
    link_data: LinkDataCreate,
    user: Annotated[User | UserRedis, Security(get_current_user, scopes=[PermissionEnum.LINK_DATA_CREATE])],
    link_data_service: LinkDataServiceDep,
) -> LinkDataRead:
    return await link_data_service.create_record(link_data=link_data, user=user)


@link_data_router.put("/{link_data_id}", status_code=status.HTTP_202_ACCEPTED)
async def update_shorten_url(
    link_data_id: int,
    link_data: LinkDataUpdate,
    user: Annotated[
        User | UserRedis,
        Security(get_current_user, scopes=[PermissionEnum.LINK_DATA_UPDATE_ALL, PermissionEnum.LINK_DATA_UPDATE_OWN]),
    ],
    link_data_service: LinkDataServiceDep,
) -> LinkDataRead:
    return await link_data_service.update_record_by_id(link_data_id=link_data_id, link_data=link_data, user=user)


@link_data_router.delete("/{link_data_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shorten_url(
    link_data_id: int,
    user: Annotated[
        User | UserRedis,
        Security(get_current_user, scopes=[PermissionEnum.LINK_DATA_DELETE_OWN, PermissionEnum.LINK_DATA_DELETE_ALL]),
    ],
    link_data_service: LinkDataServiceDep,
) -> Response:
    await link_data_service.delete_record_by_id(link_data_id=link_data_id, user=user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
