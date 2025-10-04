from abc import ABC, abstractmethod


class AbcSettingsService(ABC):
    @abstractmethod
    async def get_value(self, key: str) -> str | None:
        """Return settings value by key"""
