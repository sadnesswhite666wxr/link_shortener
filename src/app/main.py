from contextlib import asynccontextmanager

import redis
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from src.app.api.endpoints.auth import auth_router
from src.app.api.endpoints.link_data import link_data_router
from src.app.api.endpoints.permissions import permissions_router
from src.app.api.endpoints.redirect import redirect_router
from src.app.api.endpoints.roles import roles_router
from src.app.api.endpoints.system import system_router
from src.app.api.endpoints.user_role import user_role_router
from src.app.api.endpoints.users import user_router
from src.app.config.settings import get_settings
from src.app.core.logger import logger, setup_logger
from src.app.core.redis.redis import get_redis_client

setup_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = get_redis_client()
    try:
        await client.ping()
        await client.delete(f"users:{settings.DB_ADMIN_USERNAME}")
        await client.delete(f"users:{settings.DB_USER_USERNAME}")
        logger.info("redis_connected_successfully")
    except redis.exceptions.ConnectionError:
        logger.error("redis_connection_failed", detail="Redis service is unavailable")
    yield
    await client.aclose()
    logger.info("application_shutdown_complete")


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(roles_router)
app.include_router(user_router)
app.include_router(user_role_router)
app.include_router(link_data_router)
app.include_router(redirect_router)
app.include_router(permissions_router)
app.include_router(system_router)

Instrumentator().instrument(app)
