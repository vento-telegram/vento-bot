import logging
from typing import Tuple

from bot.entities.user import UserDTO, UserEntity
from bot.interfaces.services.user import AbcUserService
from bot.interfaces.uow import AbcUnitOfWork
from aiogram.types import User as TelegramUser

logger = logging.getLogger(__name__)

class UserService(AbcUserService):
    def __init__(self, uow: AbcUnitOfWork):
        self._uow = uow

    async def is_user_new(self, telegram_user: TelegramUser) -> Tuple[UserEntity, bool]:
        user_data = UserDTO(telegram_id=telegram_user.id, username=telegram_user.username)
        async with self._uow:
            user, is_new = await self._uow.user.get_or_create(user_data)

        if is_new:
            logger.info(f"New user registered: {user.telegram_id}")

        return user, is_new
