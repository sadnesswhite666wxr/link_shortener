from typing import Annotated

import structlog
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select
from starlette import status

from src.app.database.session import DBSession
from src.app.models import Role, User
from src.app.models.schemas.user import UserAddRole, UserRemoveRole, UserWithRoles
from src.app.services.redis import RedisService, RedisServiceDep

logger = structlog.get_logger()


class UserRoleService:
    def __init__(self, session: AsyncSession, redis_service: RedisService):
        self.session = session
        self.redis = redis_service

    async def add_user_role(self, user_id: int, user_roles: UserAddRole) -> UserWithRoles:
        user_query = select(User).where(User.id == user_id).options(selectinload(User.roles))
        result = await self.session.execute(user_query)
        user_db = result.scalar_one_or_none()
        if user_db is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        unique_role_ids = set(user_roles.roles)
        role_query = select(Role).where(Role.id.in_(unique_role_ids))
        result = await self.session.execute(role_query)
        role_db = result.scalars().all()

        unique_roles_db = {role.id for role in role_db}
        not_founds_roles = unique_role_ids.difference(unique_roles_db)
        if not_founds_roles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Not found roles: {', '.join([str(role_id) for role_id in not_founds_roles])}",
            )

        existing_user_roles = {role.id for role in user_db.roles}
        updated_user_roles = [role for role in role_db if role.id not in existing_user_roles]
        user_db.roles.extend(updated_user_roles)

        await logger.ainfo(
            "user_roles_added",
            target_user_id=user_id,
            target_username=user_db.username,
            added_role_ids=list(unique_role_ids),
            cache_invalidated=True,
        )

        await self.session.commit()
        await self.session.refresh(user_db)

        await self.redis.delete_user_object(user_db.username)

        return UserWithRoles.model_validate(user_db)

    async def remove_role_from_user(self, user_id: int, user_roles: UserRemoveRole) -> UserWithRoles:
        user_query = select(User).where(User.id == user_id).options(selectinload(User.roles))
        result = await self.session.execute(user_query)
        user_db = result.scalar_one_or_none()
        if user_db is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        unique_role_ids = set(user_roles.roles)
        user_db.roles = [role for role in user_db.roles if role.id not in unique_role_ids]

        await logger.ainfo(
            "user_roles_removed",
            target_user_id=user_id,
            target_username=user_db.username,
            removed_role_ids=list(unique_role_ids),
            cache_invalidated=True,
        )

        await self.session.commit()
        await self.session.refresh(user_db)

        await self.redis.delete_user_object(user_db.username)

        return UserWithRoles.model_validate(user_db)


def get_user_role_service(session: DBSession, redis_service: RedisServiceDep) -> UserRoleService:
    return UserRoleService(session=session, redis_service=redis_service)


UserRoleServiceDep = Annotated[UserRoleService, Depends(get_user_role_service)]
