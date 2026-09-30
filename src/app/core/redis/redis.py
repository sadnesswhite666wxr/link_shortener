import os

from redis.asyncio import Redis

from src.app.config.settings import get_settings

settings = get_settings()


redis_client = Redis.from_url(
    os.getenv("REDIS_URL", settings.REDIS_URL),
    decode_responses=False,
    retry_on_timeout=True,
    socket_keepalive=True,
    health_check_interval=10,
)


def get_redis_client() -> Redis:
    return redis_client
