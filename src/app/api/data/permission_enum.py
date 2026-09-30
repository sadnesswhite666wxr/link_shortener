from enum import StrEnum


class PermissionEnum(StrEnum):
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    ROLE_READ = "role:read"
    ROLE_CREATE = "role:create"
    ROLE_UPDATE = "role:update"
    ROLE_DELETE = "role:delete"

    LINK_DATA_READ_OWN = "link:read_own"
    LINK_DATA_READ_ALL = "link:read_all"
    LINK_DATA_CREATE = "link:create"
    LINK_DATA_UPDATE_ALL = "link:update_all"
    LINK_DATA_UPDATE_OWN = "link:update_own"
    LINK_DATA_DELETE_ALL = "link:delete_all"
    LINK_DATA_DELETE_OWN = "link:delete_own"

    USER_ROLE_CREATE = "user_role:create"
    USER_ROLE_DELETE = "user_role:delete"

    PERMISSION_READ = "permission:read"
