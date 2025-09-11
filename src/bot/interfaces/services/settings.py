from abc import ABC, abstractmethod


class AbcSettingsService(ABC):
    @abstractmethod
    async def get_value(self, key: str) -> int:
        """Return settings value by key"""
