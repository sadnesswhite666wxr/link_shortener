from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..config.settings import get_settings

settings = get_settings()

engine = create_async_engine(url=settings.DB_URL, pool_size=50, max_overflow=100, pool_recycle=1800, pool_pre_ping=True)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


DBSession = Annotated[AsyncSession, Depends(get_session)]
