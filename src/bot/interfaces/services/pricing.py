from abc import ABC, abstractmethod

from bot.enums import BotModeEnum, ModelNameEnum


class AbcPricingService(ABC):
    @abstractmethod
    async def get_price_for_model(self, model: ModelNameEnum) -> int:
        """Return price in tokens for a given model"""

    @abstractmethod
    async def ensure_user_can_afford(self, user_balance: int, model: ModelNameEnum) -> bool:
        """Return True if the star balance is enough for at least one request in given mode."""
