import os
from enum import Enum

from pwdlib import PasswordHash
from sqlalchemy import create_engine
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from src.app.models import Permission, Role, User

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DB_ADMIN_USERNAME = os.getenv("DB_ADMIN_USERNAME")
DB_ADMIN_PASSWORD = os.getenv("DB_ADMIN_PASSWORD")
DB_ADMIN_EMAIL = os.getenv("DB_ADMIN_EMAIL")

DB_USER_USERNAME = os.getenv("DB_USER_USERNAME")
DB_USER_PASSWORD = os.getenv("DB_USER_PASSWORD")
DB_USER_EMAIL = os.getenv("DB_USER_EMAIL")

DB_USER_ROLE_NAME = "user"
DB_ADMIN_ROLE_NAME = "admin"

DB_USER_ROLE_DESC = "Regular user"
DB_ADMIN_ROLE_DESC = "Administrator with all existing permissions"

password_hash = PasswordHash.recommended()

engine = create_engine(url=f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@postgres:5432/{DB_NAME}")


class AllPermissions(Enum):
    USER_CREATE = ("user", "create")
    USER_READ = ("user", "read")
    USER_UPDATE = ("user", "update")
    USER_DELETE = ("user", "delete")
    ROLE_CREATE = ("role", "create")
    ROLE_READ = ("role", "read")
    ROLE_UPDATE = ("role", "update")
    ROLE_DELETE = ("role", "delete")
    LINK_CREATE = ("link", "create")
    LINK_READ_OWN = ("link", "read_own")
    LINK_READ_ALL = ("link", "read_all")
    LINK_UPDATE_OWN = ("link", "update_own")
    LINK_UPDATE_ALL = ("link", "update_all")
    LINK_DELETE_OWN = ("link", "delete_own")
    LINK_DELETE_ALL = ("link", "delete_all")
    USER_ROLE_CREATE = ("user_role", "create")
    USER_ROLE_DELETE = ("user_role", "delete")
    PERMISSION_READ = ("permission", "read")

    def __getitem__(self, index):
        return self.value[index]


AdminPermissions = [permission for permission in AllPermissions]

UserPermissions = [
    AllPermissions.LINK_CREATE,
    AllPermissions.LINK_READ_OWN,
    AllPermissions.LINK_UPDATE_OWN,
    AllPermissions.LINK_DELETE_OWN,
]


class DBFiller:
    def __init__(self, session: Session):
        self.session = session

    def _create_permissions(self):
        for permission in AllPermissions:
            resource, action = permission[0], permission[1]
            exists = self.session.exec(
                select(Permission).where(Permission.action == action).where(Permission.resource == resource)
            ).first()
            if not exists:
                self.session.add(Permission(resource=resource, action=action))

        self.session.commit()

    def _create_roles(self):
        for role_name, desc in [(DB_USER_ROLE_NAME, DB_USER_ROLE_DESC), (DB_ADMIN_ROLE_NAME, DB_ADMIN_ROLE_DESC)]:
            exists = self.session.exec(select(Role).where(Role.name == role_name)).first()
            if not exists:
                self.session.add(Role(name=role_name, description=desc))

        self.session.commit()

    def _create_users(self):
        for username, email, password in [
            (DB_USER_USERNAME, DB_USER_EMAIL, DB_USER_PASSWORD),
            (DB_ADMIN_USERNAME, DB_ADMIN_EMAIL, DB_ADMIN_PASSWORD),
        ]:
            exists = self.session.exec(select(User).where(User.username == username)).first()
            if not exists:
                self.session.add(User(username=username, email=email, hashed_password=password_hash.hash(password)))

        self.session.commit()

    def _link_roles_with_permissions(self):
        for role_name, permissions in [
            (DB_ADMIN_ROLE_NAME, AdminPermissions),
            (DB_USER_ROLE_NAME, UserPermissions),
        ]:
            role = self.session.exec(
                select(Role).where(Role.name == role_name).options(selectinload(Role.permissions))
            ).first()
            permission_list = []
            for permission in permissions:
                resource, action = permission[0], permission[1]
                db_permission = self.session.exec(
                    select(Permission).where(Permission.action == action).where(Permission.resource == resource)
                ).first()
                permission_list.append(db_permission)

            role.permissions = permission_list

        self.session.commit()

    def _link_users_with_roles(self):
        for username, role_name in [
            (DB_USER_USERNAME, DB_USER_ROLE_NAME),
            (DB_ADMIN_USERNAME, DB_ADMIN_ROLE_NAME),
        ]:
            user = self.session.exec(
                select(User).where(User.username == username).options(selectinload(User.roles))
            ).first()
            role = self.session.exec(select(Role).where(Role.name == role_name)).first()
            user.roles = [
                role,
            ]
            self.session.commit()

    def fill_database_with_data(self):
        self._create_permissions()
        self._create_roles()
        self._create_users()
        self._link_roles_with_permissions()
        self._link_users_with_roles()


def main():
    with Session(engine) as session:
        db_object = DBFiller(session)
        db_object.fill_database_with_data()


main()
