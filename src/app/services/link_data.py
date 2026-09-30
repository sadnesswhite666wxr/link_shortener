from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from starlette import status

from src.app.api.data.permission_enum import PermissionEnum
from src.app.database.session import DBSession
from src.app.models import LinkData, User
from src.app.models.schemas.link_data import (
    LinkDataCreate,
    LinkDataRead,
    LinkDataRedis,
    LinkDataUpdate,
)
from src.app.services.redis import RedisService, RedisServiceDep
from src.app.utils.user_scopes import extract_scopes_from_user


class LinkDataService:
    def __init__(self, session: AsyncSession, redis_service: RedisService):
        self.session = session
        self.redis = redis_service

    async def get_record_by_id(self, user: User, link_data_id: int) -> LinkDataRead | None:
        user_scopes = extract_scopes_from_user(user)

        link_data = await self.redis.get_link_data(link_data_id)

        if link_data is None:
            link_data = select(LinkData).where(LinkData.id == link_data_id)
            link_data = await self.session.execute(link_data)
            link_data = link_data.scalar_one_or_none()

            if link_data is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LinkData not found")

            link_data = LinkDataRedis.model_validate(link_data)
            await self.redis.set_link_data(link_data)

        if PermissionEnum.LINK_DATA_READ_ALL not in user_scopes:
            has_permission = PermissionEnum.LINK_DATA_READ_OWN in user_scopes
            is_owner = link_data.created_by == user.id
            if not (has_permission and is_owner):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

        return LinkDataRead.model_validate(link_data)

    async def get_all_visible_records(self, user: User) -> list[LinkDataRead]:
        user_scopes = extract_scopes_from_user(user)
        data_query = select(LinkData)

        if PermissionEnum.LINK_DATA_READ_ALL not in user_scopes:
            if PermissionEnum.LINK_DATA_READ_OWN not in user_scopes:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
            data_query = data_query.where(LinkData.created_by == user.id)

        result = await self.session.execute(data_query)
        link_data = result.scalars().all()
        return [LinkDataRead.model_validate(record) for record in link_data]

    async def create_record(self, link_data: LinkDataCreate, user: User) -> LinkData:
        new_link_data = link_data.model_dump()
        new_link_data["created_by"] = user.id
        db_link = LinkData.model_validate(new_link_data)

        self.session.add(db_link)
        await self.session.commit()
        await self.session.refresh(db_link)

        link_data_redis = LinkDataRedis.model_validate(db_link)
        await self.redis.set_link_data(link_data_redis)

        return db_link

    async def update_record_by_id(self, link_data: LinkDataUpdate, user: User, link_data_id: int) -> LinkDataRead:
        data_query = select(LinkData).where(LinkData.id == link_data_id)
        user_scopes = extract_scopes_from_user(user)
        db_link = await self.session.execute(data_query)
        db_link = db_link.scalar_one_or_none()

        if db_link is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LinkData not found")

        if PermissionEnum.LINK_DATA_UPDATE_ALL not in user_scopes:
            has_permission = PermissionEnum.LINK_DATA_UPDATE_OWN in user_scopes
            is_owner = db_link.created_by == user.id
            if not (has_permission and is_owner):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

        db_link.sqlmodel_update(link_data)

        await self.session.commit()
        await self.session.refresh(db_link)

        await self.redis.delete_link_data(link_data_id)

        return LinkDataRead.model_validate(db_link)

    async def delete_record_by_id(self, link_data_id: int, user: User) -> None:
        data_query = select(LinkData).where(LinkData.id == link_data_id)
        user_scopes = extract_scopes_from_user(user)

        db_link = await self.session.execute(data_query)
        db_link = db_link.scalar_one_or_none()
        if db_link is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LinkData not found")

        if PermissionEnum.LINK_DATA_DELETE_ALL not in user_scopes:
            has_permission = PermissionEnum.LINK_DATA_DELETE_OWN in user_scopes
            is_owner = db_link.created_by == user.id
            if not (has_permission and is_owner):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

        await self.session.delete(db_link)
        await self.session.commit()
        await self.redis.delete_link_data(link_data_id)


def get_link_data_service(session: DBSession, redis: RedisServiceDep) -> LinkDataService:
    return LinkDataService(session=session, redis_service=redis)


LinkDataServiceDep = Annotated[LinkDataService, Depends(get_link_data_service)]
