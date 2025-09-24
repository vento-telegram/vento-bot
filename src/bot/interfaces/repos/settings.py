from abc import abstractmethod

from bot.entities.settings import SettingsEntity
from bot.interfaces.repos.base import AbcRepo


class AbcSettingsRepo(AbcRepo[SettingsEntity]):
    @abstractmethod
    async def get_by_key(self, key: str) -> SettingsEntity | None:
        """Fetch a model price by programmatic key (e.g., 'gpt5')."""

    @abstractmethod
    async def list_all(self) -> dict[str, str]:
        """Return all settings as dict key->value."""

    @abstractmethod
    async def set_value(self, key: str, value: str) -> None:
        """Set or create setting value by key."""
