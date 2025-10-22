from abc import abstractmethod
from datetime import date

from bot.entities.transaction import TransactionEntity
from bot.interfaces.repos.base import AbcRepo
from bot.schemas import RequestsCounts, UserTotals


class AbcTransactionRepo(AbcRepo[TransactionEntity]):
    @abstractmethod
    async def add(self, entry: TransactionEntity) -> TransactionEntity:
        ...

    @abstractmethod
    async def update_meta_by_id(self, transaction_id: int, meta: str) -> TransactionEntity | None:
        ...

    # Aggregations
    @abstractmethod
    async def total_spent_today(self) -> int:
        """Total stars (â­) spent across all users today (sum of negative deltas as positive)."""

    @abstractmethod
    async def requests_count_today(self) -> int:
        """Total number of requests recorded today (count of negative deltas)."""

    @abstractmethod
    async def requests_by_model_today(self) -> RequestsCounts:
        """Requests count today grouped by model key inferred from reason (gpt-5, gpt-5-mini)."""

    @abstractmethod
    async def count_active_users_today(self) -> int:
        """Number of unique users who made at least one paid request today (MSK day)."""
    @abstractmethod
    async def user_totals(self, user_id: int) -> UserTotals:
        """Per-user totals: all-time spent, today spent, per-model all-time counts, last request time."""

    @abstractmethod
    async def list_today_by_reasons(self, reasons: list[str]) -> list[TransactionEntity]:
        """List today's transactions filtered by a set of reasons."""

    @abstractmethod
    async def list_by_date_by_reasons(self, day: date, reasons: list[str]) -> list[TransactionEntity]:
        """List transactions for a specific calendar date filtered by a set of reasons."""


