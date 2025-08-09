from abc import abstractmethod

from bot.entities.ledger import LedgerEntity
from bot.schemas import RequestsCounts, UserTotals
from bot.interfaces.repos.base import AbcRepo


class AbcLedgerRepo(AbcRepo[LedgerEntity]):
    @abstractmethod
    async def add(self, entry: LedgerEntity) -> LedgerEntity:
        ...

    @abstractmethod
    async def update_meta_by_id(self, ledger_id: int, meta: str) -> LedgerEntity | None:
        ...

    # Aggregations
    @abstractmethod
    async def total_spent_today(self) -> int:
        """Total tokens spent across all users today (sum of negative deltas as positive)."""

    @abstractmethod
    async def requests_count_today(self) -> int:
        """Total number of requests recorded today (count of negative deltas)."""

    @abstractmethod
    async def requests_by_model_today(self) -> RequestsCounts:
        """Requests count today grouped by model key inferred from reason (gpt-5, gpt-5-mini, dalle3)."""

    @abstractmethod
    async def user_totals(self, user_id: int) -> UserTotals:
        """Per-user totals: all-time spent, today spent, per-model all-time counts, last request time."""


