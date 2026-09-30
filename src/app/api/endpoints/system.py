import prometheus_client
import structlog
from fastapi import APIRouter, HTTPException
from redis import RedisError
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select
from starlette import status
from starlette.responses import JSONResponse, Response

from src.app.config.settings import get_settings
from src.app.database.session import DBSession
from src.app.services.redis import RedisServiceDep

settings = get_settings()

system_router = APIRouter(
    prefix="/system",
)


logger = structlog.get_logger()


@system_router.get(settings.METRICS_PATH, include_in_schema=False)
def metrics() -> Response:
    return Response(content=prometheus_client.generate_latest(), media_type=prometheus_client.CONTENT_TYPE_LATEST)


@system_router.get("/health", status_code=status.HTTP_200_OK)
async def health(
    redis: RedisServiceDep,
    session: DBSession,
) -> JSONResponse:
    try:
        await session.execute(select(1))
        await redis.ping()
        return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ok"})

    except (SQLAlchemyError, RedisError) as e:
        await logger.acritical("infrastructure_healthcheck_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Unexpected error")
