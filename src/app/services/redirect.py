from typing import Annotated

import structlog
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.app.api.data.permission_enum import PermissionEnum
from src.app.database.session import DBSession
from src.app.models import LinkData, User
from src.app.models.schemas.link_data import LinkDataRedis
from src.app.services.redis import RedisService, RedisServiceDep
from src.app.utils.base62 import decode_base62
from src.app.utils.user_scopes import extract_scopes_from_user

logger = structlog.get_logger()


class RedirectService:
    def __init__(self, session: AsyncSession, redis_service: RedisService):
        self.session = session
        self.redis = redis_service

    async def redirect(self, link_data_shorten: str, user: User) -> str:
        user_scopes = extract_scopes_from_user(user)

        record_data = await self.redis.get_link_data(link_data_shorten)
        if record_data is None:
            await logger.ainfo("cache_miss_redirect", shorten_code=link_data_shorten, user_id=user.id)

            try:
                record_id = decode_base62(link_data_shorten)
            except ValueError:
                raise HTTPException(status_code=404, detail="Invalid link format")

            query = select(LinkData).where(LinkData.id == record_id)
            result = await self.session.execute(query)
            db_record = result.scalar_one_or_none()
            if db_record is None:
                raise HTTPException(status_code=404, detail="Link data not found")

            record_data = LinkDataRedis.model_validate(db_record)
            await self.redis.set_link_data(record_data)

        if PermissionEnum.LINK_DATA_READ_ALL not in user_scopes:
            has_permission = PermissionEnum.LINK_DATA_READ_OWN in user_scopes
            is_owner = record_data.created_by == user.id
            if not (has_permission and is_owner):
                await logger.aerror(
                    "unauthorized_access_attempt",
                    user_id=user.id,
                    resource_id=record_data.id,
                    shorten_code=link_data_shorten,
                    user_scopes=list(user_scopes),
                )

                raise HTTPException(status_code=403, detail="Not enough permissions")

        return record_data.origin


def get_redirect_service(session: DBSession, redis_service: RedisServiceDep) -> RedirectService:
    return RedirectService(session, redis_service)


RedirectServiceDep = Annotated[RedirectService, Depends(get_redirect_service)]
