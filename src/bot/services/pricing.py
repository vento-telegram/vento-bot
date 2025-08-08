from bot.enums import BotModeEnum
from bot.interfaces.services.pricing import AbcPricingService
from bot.interfaces.uow import AbcUnitOfWork


class PricingService(AbcPricingService):
    def __init__(self, uow: AbcUnitOfWork):
        self._uow = uow

    @staticmethod
    def _mode_to_key(mode: BotModeEnum) -> str:
        mapping = {
            BotModeEnum.gpt5: "gpt-5",
            BotModeEnum.gpt5_mini: "gpt-5-mini",
            BotModeEnum.dalle3: "dalle3",
            BotModeEnum.veo: "veo3",
        }
        return mapping.get(mode, "unknown")

    async def get_price_for_mode(self, mode: BotModeEnum) -> int:
        key = self._mode_to_key(mode)
        async with self._uow:
            price = await self._uow.price.get_by_key(key)
        return price.price if price else 0
