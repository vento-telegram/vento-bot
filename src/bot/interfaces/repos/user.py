from abc import abstractmethod

from bot.entities.user import UserDTO, UserEntity
from bot.interfaces.repos.base import AbcRepo


class AbcUserRepo(AbcRepo[UserEntity]):
    @abstractmethod
    async def get_or_create(self, user: UserDTO) -> tuple[UserEntity, bool]:
        """Get or create a user entity."""

    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: int) -> UserEntity | None:
        """Fetch a user by Telegram ID or return None if not found."""

    @abstractmethod
    async def update_balance_by_user_id(self, user_id: int, delta: int) -> UserEntity | None:
        """Atomically update balance for a user by id and return updated entity."""

    @abstractmethod
    async def get_by_username(self, username: str) -> UserEntity | None:
        """Fetch a user by username or return None if not found."""

    @abstractmethod
    async def set_blocked_by_username(self, username: str, is_blocked: bool) -> UserEntity | None:
        """Block or unblock a user by username and return updated entity, or None if not found."""