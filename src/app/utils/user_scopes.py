from src.app.models import User
from src.app.models.schemas.user import UserRedis


def extract_scopes_from_user(user: User | UserRedis) -> list[str]:
    if isinstance(user, UserRedis):
        return user.permissions

    user_scopes = []
    for role in user.roles or []:
        for permission in role.permissions or []:
            user_scopes.append(f"{permission.resource}:{permission.action}")

    return list(set(user_scopes))
