from abc import ABC, abstractmethod
from typing import Tuple

from aiogram.types import User as TelegramUser

from bot.entities.user import UserEntity


class AbcUserService(ABC):
    @abstractmethod
    async def is_user_new(self, telegram_user: TelegramUser) -> Tuple[UserEntity, bool]:
        ...

    @abstractmethod
    async def get_user(self, telegram_id: int) -> UserEntity | None:
        ...