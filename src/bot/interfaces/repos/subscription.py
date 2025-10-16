from abc import abstractmethod

from bot.entities.subscription import SubscriptionEntity
from bot.interfaces.repos.base import AbcRepo


class AbcSubscriptionRepo(AbcRepo[SubscriptionEntity]):
    @abstractmethod
    async def get_active_by_user_id(self, user_id: int) -> SubscriptionEntity | None:
        """Return active subscription where till >= now()."""

    @abstractmethod
    async def get_latest_by_user_id(self, user_id: int) -> SubscriptionEntity | None:
        """Return latest subscription for user (any till)."""

    @abstractmethod
    async def create(self, user_id: int, till) -> SubscriptionEntity:
        """Create subscription with given till."""

    @abstractmethod
    async def update_counts(self, sub_id: int, requests_count: int | None, mini_requests_count: int | None) -> SubscriptionEntity | None:
        """Update counters and return updated entity."""

    @abstractmethod
    async def update_till(self, sub_id: int, till) -> SubscriptionEntity | None:
        """Update till and return updated entity."""

