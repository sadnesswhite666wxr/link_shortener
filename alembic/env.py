import os
import asyncio
from pathlib import Path
from logging.config import fileConfig
from dotenv import load_dotenv

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from sqlmodel import SQLModel

# Загружаем .env из корня проекта
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from src.app.models import *

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Offline mode — без подключения к БД, только генерация скрипта."""
    url = os.getenv("DB_URL")
    if not url:
        raise ValueError("Переменная DB_URL не найдена в .env")

    config.set_main_option("sqlalchemy.url", url)

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # полезно для детекции изменений типов колонок
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Вспомогательная функция для запуска миграций в синхронном контексте."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """Асинхронная версия запуска миграций."""
    # Берём URL из .env
    db_url = os.getenv("DB_URL")
    if not db_url:
        raise ValueError("Переменная DB_URL не найдена в .env")

    # Создаём асинхронный движок
    connectable = async_engine_from_config(
        {"sqlalchemy.url": db_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # run_sync() позволяет вызвать синхронную функцию внутри async-контекста
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Online mode — с подключением к БД."""
    # Запускаем асинхронную логику через asyncio.run()
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
