from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis

from src.app.config.settings import get_settings
from src.app.core.redis.redis import get_redis_client
from src.app.models import User
from src.app.models.schemas.link_data import LinkDataRedis
from src.app.models.schemas.user import UserRedis
from src.app.utils.base62 import encode_base62
from src.app.utils.user_scopes import extract_scopes_from_user

settings = get_settings()


class RedisService:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.cache_ttl = settings.redis_ttl_sec

    async def ping(self) -> bool:
        return await self.redis.ping()

    def _get_user_key(self, username: str) -> str:
        return f"users:{username}"

    def _get_link_data_key(self, short_url: str) -> str:
        return f"link_data:{short_url}"

    async def set_user_object(self, user: User):
        key = self._get_user_key(user.username)
        user_permissions = extract_scopes_from_user(user)
        user_data = UserRedis.model_validate(user, update={"permissions": user_permissions})
        await self.redis.set(key, user_data.model_dump_json(), ex=self.cache_ttl)

    async def get_user_object(self, username: str) -> UserRedis | None:
        key = self._get_user_key(username)
        user_data = await self.redis.get(key)
        if not user_data:
            return None

        return UserRedis.model_validate_json(user_data.decode("utf-8") if isinstance(user_data, bytes) else user_data)

    async def set_link_data(self, link_data: LinkDataRedis):

        key = self._get_link_data_key(link_data.shorten)
        await self.redis.set(key, link_data.model_dump_json(exclude={"shorten"}), ex=self.cache_ttl)

    async def get_link_data(self, short_url_or_id: str | int) -> LinkDataRedis | None:
        if isinstance(short_url_or_id, int):
            short_url = encode_base62(short_url_or_id)
        else:
            short_url = short_url_or_id

        key = self._get_link_data_key(short_url)
        link_data = await self.redis.get(key)
        if not link_data:
            return None

        return LinkDataRedis.model_validate_json(
            link_data.decode("utf-8") if isinstance(link_data, bytes) else link_data
        )

    async def delete_link_data(self, short_url_or_id: str | int) -> None:
        if isinstance(short_url_or_id, int):
            short_url = encode_base62(short_url_or_id)
        else:
            short_url = short_url_or_id

        key = self._get_link_data_key(short_url)
        await self.redis.delete(key)

    async def delete_user_object(self, username: str) -> None:
        key = self._get_user_key(username)
        await self.redis.delete(key)


def get_redis_service() -> RedisService:
    return RedisService(redis=get_redis_client())


RedisServiceDep = Annotated[RedisService, Depends(get_redis_service)]
