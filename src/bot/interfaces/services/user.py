from abc import ABC, abstractmethod
from typing import Tuple

from aiogram.types import User as TelegramUser

from bot.entities.user import UserEntity
from bot.enums import TransactionReasonEnum


class AbcUserService(ABC):
    @abstractmethod
    async def is_user_new(self, telegram_user: TelegramUser, ref_from: str | None = None) -> Tuple[UserEntity, bool]:
        ...

    @abstractmethod
    async def get_user(self, telegram_id: int) -> UserEntity | None:
        ...

    @abstractmethod
    async def add_tokens_by_username(self, username: str, amount: int, reason: TransactionReasonEnum) -> UserEntity | None:
        """Increase user's balance by username and write a transaction entry."""

    @abstractmethod
    async def add_tokens_by_telegram_id(self, telegram_id: int, amount: int, reason: TransactionReasonEnum) -> UserEntity | None:
        """Increase user's balance by telegram_id and write a transaction entry."""

    @abstractmethod
    async def block_user_by_username(self, username: str) -> UserEntity | None:
        ...

    @abstractmethod
    async def unblock_user_by_username(self, username: str) -> UserEntity | None:
        ...

    @abstractmethod
    async def daily_min_balance_topup(self, min_balance: int) -> int:
        """Ensure all users have at least min_balance tokens; return updated users count."""

    @abstractmethod
    async def list_admins(self) -> list[UserEntity]:
        """Return all users with is_admin flag enabled."""

    @abstractmethod
    async def list_telegram_ids(self) -> list[int]:
        """Return telegram_id values for all users."""