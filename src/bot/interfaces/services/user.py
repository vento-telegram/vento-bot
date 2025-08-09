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

    @abstractmethod
    async def add_tokens_by_username(self, username: str, amount: int, reason: str) -> UserEntity | None:
        """Increase user's balance by username and write a ledger entry. Returns updated user or None."""

    @abstractmethod
    async def block_user_by_username(self, username: str) -> UserEntity | None:
        ...

    @abstractmethod
    async def unblock_user_by_username(self, username: str) -> UserEntity | None:
        ...