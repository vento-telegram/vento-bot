from abc import abstractmethod

from bot.entities.model_price import PriceEntity
from bot.interfaces.repos.base import AbcRepo


class AbcPriceRepo(AbcRepo[PriceEntity]):
    @abstractmethod
    async def get_by_key(self, key: str) -> PriceEntity | None:
        """Fetch a model price by programmatic key (e.g., 'gpt5')."""
