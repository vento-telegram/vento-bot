from abc import abstractmethod

from bot.entities.settings import SettingsEntity
from bot.interfaces.repos.base import AbcRepo


class AbcSettingsRepo(AbcRepo[SettingsEntity]):
    @abstractmethod
    async def get_by_key(self, key: str) -> SettingsEntity | None:
        """Fetch a model price by programmatic key (e.g., 'gpt5')."""
