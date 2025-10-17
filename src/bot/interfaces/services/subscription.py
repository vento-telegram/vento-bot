from abc import ABC, abstractmethod
from bot.entities.subscription import SubscriptionEntity


class AbcSubscriptionService(ABC):
    @abstractmethod
    async def get_active_by_user_id(self, user_id: int) -> SubscriptionEntity | None:
        """Return active subscription for user or None."""

    @abstractmethod
    async def activate_or_extend_for_telegram(self, telegram_id: int, days: int, bonus_tokens: int) -> SubscriptionEntity | None:
        """Create or extend subscription by telegram_id; also credit bonus tokens."""

    @abstractmethod
    async def mark_and_check_limit(self, user_id: int, mode: str) -> bool:
        """Increment daily counter for mode if within limit; return True if allowed."""

