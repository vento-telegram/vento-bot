from abc import abstractmethod

from bot.entities.ledger import LedgerEntity
from bot.interfaces.repos.base import AbcRepo


class AbcLedgerRepo(AbcRepo[LedgerEntity]):
    @abstractmethod
    async def add(self, entry: LedgerEntity) -> LedgerEntity:
        ...

    @abstractmethod
    async def list_for_user(self, user_id: int, limit: int = 20) -> list[LedgerEntity]:
        ...


