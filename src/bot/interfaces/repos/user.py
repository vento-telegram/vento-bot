from abc import abstractmethod

from bot.entities.user import UserDTO, UserEntity
from bot.interfaces.repos.base import AbcRepo


class AbcUserRepo(AbcRepo[UserEntity]):
    @abstractmethod
    async def get_or_create(self, user: UserDTO) -> tuple[UserEntity, bool]:
        """Get or create a user entity."""
