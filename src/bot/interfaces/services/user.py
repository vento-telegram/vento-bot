from abc import ABC, abstractmethod

from aiogram.types import User as TelegramUser


class AbcUserService(ABC):
    @abstractmethod
    async def is_user_new(self, telegram_user: TelegramUser) -> bool:
        ...
