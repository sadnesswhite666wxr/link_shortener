from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select
from starlette import status

from src.app.database.session import DBSession
from src.app.models import Permission, Role
from src.app.models.schemas.role import (
    RoleCreate,
    RoleRead,
    RoleUpdate,
    RoleWithPermission,
)
from src.app.services.redis import RedisService, RedisServiceDep


class RoleService:
    def __init__(self, session: AsyncSession, redis_service: RedisService) -> None:
        self.session = session
        self.redis = redis_service

    async def _validate_permissions(self, updated_role: RoleUpdate | RoleCreate) -> list[Permission]:
        if not updated_role.permissions:
            return []

        income_unique_perm_ids = set(updated_role.permissions)
        exist_permissions = await self.session.execute(
            select(Permission).where(Permission.id.in_(income_unique_perm_ids))
        )
        exist_permissions = exist_permissions.scalars().all()
        permission_diff = income_unique_perm_ids.difference({permission.id for permission in exist_permissions})
        if permission_diff:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Not found permissions: {list(permission_diff)}"
            )

        return exist_permissions

    async def get_role_with_permission(self, role_id: int) -> RoleWithPermission:
        role_query = select(Role).where(Role.id == role_id).options(selectinload(Role.permissions))
        result = await self.session.execute(role_query)
        db_role = result.scalar_one_or_none()
        if db_role is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

        return RoleWithPermission.model_validate(db_role)

    async def get_all_roles(self) -> list[RoleRead]:
        role_query = select(Role)
        result = await self.session.execute(role_query)
        db_roles = result.scalars().all()
        return [RoleRead.model_validate(db_role) for db_role in db_roles]

    async def create_role(self, role: RoleCreate) -> RoleWithPermission:
        exists_permissions = await self._validate_permissions(role)
        role_query = select(Role).where(Role.name == role.name)
        result = await self.session.execute(role_query)
        db_role = result.scalar_one_or_none()
        if db_role is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role already exists")

        role_data = role.model_dump(exclude={"permissions"})
        new_role = Role.model_validate(role_data)
        new_role.permissions = exists_permissions

        self.session.add(new_role)
        await self.session.commit()
        await self.session.refresh(new_role)

        return RoleWithPermission.model_validate(new_role)

    async def update_role(self, role_id: int, updated_role: RoleUpdate) -> RoleWithPermission:
        role_query = (
            select(Role).where(Role.id == role_id).options(selectinload(Role.permissions), selectinload(Role.users))
        )
        result = await self.session.execute(role_query)
        db_role = result.scalar_one_or_none()
        if db_role is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

        role_data = updated_role.model_dump(exclude={"permissions"}, exclude_unset=True)
        db_role.sqlmodel_update(role_data)

        if updated_role.permissions is not None:
            exists_permissions = await self._validate_permissions(updated_role)
            db_role.permissions = exists_permissions

        invalidate_users = [user.username for user in db_role.users]

        await self.session.commit()
        await self.session.refresh(db_role)

        if invalidate_users:
            for username in invalidate_users:
                await self.redis.delete_user_object(username)

        return RoleWithPermission.model_validate(db_role)

    async def delete_role(self, role_id: int) -> None:
        role_query = select(Role).where(Role.id == role_id).options(selectinload(Role.users))
        result = await self.session.execute(role_query)
        db_role = result.scalar_one_or_none()
        if db_role is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

        invalidate_users = [user.username for user in db_role.users]

        await self.session.delete(db_role)
        await self.session.commit()

        if invalidate_users:
            for username in invalidate_users:
                await self.redis.delete_user_object(username)


def get_role_service(session: DBSession, redis_service: RedisServiceDep) -> RoleService:
    return RoleService(session=session, redis_service=redis_service)


RoleServiceDep = Annotated[RoleService, Depends(get_role_service)]
