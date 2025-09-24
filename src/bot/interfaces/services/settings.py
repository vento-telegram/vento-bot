from abc import ABC, abstractmethod


class AbcSettingsService(ABC):
    @abstractmethod
    async def get_value(self, key: str) -> int:
        """Return settings value by key"""

    @abstractmethod
    async def list_all(self) -> dict[str, str]:
        """Return all settings as a dict key -> value."""

    @abstractmethod
    async def set_value(self, key: str, value: str) -> None:
        """Upsert a setting value by key."""
