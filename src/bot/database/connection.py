from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Callable

import orjson
from pydantic_core import to_jsonable_python as pydantic_encoder
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from bot.settings import PostgresSettings
from bot.settings import settings as config


def orjson_dumps(value: Any, *, default: Callable[[Any], Any] = pydantic_encoder) -> str:
    return orjson.dumps(value, default=default).decode()


class AlchemyDatabase:
    def __init__(self, settings: PostgresSettings) -> None:
        self._engine: AsyncEngine = create_async_engine(
            url=str(settings.URI),
            json_serializer=orjson_dumps,
            json_deserializer=orjson.loads,
        )
        self._session_factory = async_sessionmaker(bind=self._engine, expire_on_commit=False)

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        return self._session_factory

    @asynccontextmanager
    async def session_scope(self) -> AsyncGenerator[AsyncSession, None]:
        session = self._session_factory()

        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


db = AlchemyDatabase(config.POSTGRES)
long_operation_db = AlchemyDatabase(
    config.POSTGRES.model_copy(update={"CONNECTION_TIMEOUT": 600, "COMMAND_TIMEOUT": 600}),
)
