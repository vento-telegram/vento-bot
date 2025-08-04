from abc import ABC, abstractmethod

from aiogram.types import User as TelegramUser


class AbstractUserService(ABC):
    @abstractmethod
    async def get_start_message(self, telegram_user: TelegramUser) -> str:
        ...
