from abc import ABC, abstractmethod


class AbcSettingsService(ABC):
    @abstractmethod
    async def get_value(self, key: str) -> str:
        """Return settings value by key"""

    @abstractmethod
    async def list_all(self) -> dict[str, str]:
        ...

    @abstractmethod
    async def set_value(self, key: str, value: str) -> None:
        ...
