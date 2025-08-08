from abc import ABC, abstractmethod

from bot.enums import BotModeEnum


class AbcPricingService(ABC):
    @abstractmethod
    async def get_price_for_mode(self, mode: BotModeEnum) -> float:
        """Return price in tokens for a given mode."""
