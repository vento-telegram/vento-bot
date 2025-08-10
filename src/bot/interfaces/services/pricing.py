from abc import ABC, abstractmethod

from bot.enums import BotModeEnum


class AbcPricingService(ABC):
    @abstractmethod
    async def get_price_for_mode(self, mode: BotModeEnum) -> int:
        """Return price in stars (⭐) for a given mode."""

    @abstractmethod
    async def ensure_user_can_afford(self, user_balance: int, mode: BotModeEnum) -> bool:
        """Return True if the star balance is enough for at least one request in given mode."""
