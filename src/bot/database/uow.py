from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.interfaces.uow import AbcUnitOfWork
from bot.repos.user import UserRepo
from bot.repos.model_price import PriceRepo


class Uow(AbcUnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def __aenter__(self) -> "AbcUnitOfWork":  # type: ignore[override]
        self.session = self.session_factory()

        self.user = UserRepo(self.session)
        self.price = PriceRepo(self.session)

        return await super().__aenter__()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def shutdown(self) -> None:
        await self.session.close()
