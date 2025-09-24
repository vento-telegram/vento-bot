from bot.interfaces.services.settings import AbcSettingsService
from bot.interfaces.uow import AbcUnitOfWork


class SettingsService(AbcSettingsService):
    def __init__(self, uow: AbcUnitOfWork):
        self._uow = uow

    async def get_value(self, key: str) -> str:
        async with self._uow:
            settings = await self._uow.settings.get_by_key(key)
        return settings.value

    async def list_all(self) -> dict[str, str]:
        async with self._uow:
            return await self._uow.settings.list_all()

    async def set_value(self, key: str, value: str) -> None:
        async with self._uow:
            await self._uow.settings.set_value(key, value)
