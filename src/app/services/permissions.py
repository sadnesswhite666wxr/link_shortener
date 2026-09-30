from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.app.database.session import DBSession
from src.app.models import Permission
from src.app.models.schemas.permission import PermissionRead


class PermissionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_permissions(self) -> list[PermissionRead]:
        permission_query = select(Permission)
        result = await self.session.execute(permission_query)
        db_permissions = result.scalars().all()

        return [PermissionRead.model_validate(permission) for permission in db_permissions]


def get_permission_service(session: DBSession) -> PermissionService:
    return PermissionService(session=session)


PermissionServiceDep = Annotated[PermissionService, Depends(get_permission_service)]
