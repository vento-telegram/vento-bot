from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from bot.interfaces.repos.user import AbcUserRepo
from bot.interfaces.repos.model_price import AbcPriceRepo
from bot.interfaces.repos.ledger import AbcLedgerRepo


class AbcUnitOfWork(ABC):
    user: AbcUserRepo
    price: AbcPriceRepo
    ledger: AbcLedgerRepo

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType,
    ) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

        await self.shutdown()

    @abstractmethod
    async def commit(self) -> None:
        """Commit changes"""

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback changes"""

    @abstractmethod
    async def shutdown(self) -> None:
        """Finish opened resources work"""
