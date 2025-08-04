import asyncio
from logging.config import fileConfig

from alembic import context
from bot.database.models import metadata
from bot.settings import settings

from bot.database.connection import long_operation_db

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = metadata

config.set_main_option("sqlalchemy.url", str(settings.POSTGRES.URI))


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    async with (
        long_operation_db.engine.connect() as connection,
        asyncio.timeout(settings.POSTGRES.MIGRATION_TIMEOUT),
    ):
        await connection.run_sync(do_run_migrations)

    await long_operation_db.engine.dispose()


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = config.attributes.get("connection")

    if connectable is None:
        asyncio.run(run_async_migrations())
    else:
        do_run_migrations(connectable)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
