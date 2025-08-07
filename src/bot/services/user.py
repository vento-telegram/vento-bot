import logging

from bot.entities.user import UserDTO
from bot.interfaces.services.user import AbcUserService
from bot.interfaces.uow import AbcUnitOfWork
from aiogram.types import User as TelegramUser

logger = logging.getLogger(__name__)

class UserService(AbcUserService):
    def __init__(self, uow: AbcUnitOfWork):
        self._uow = uow

    async def is_user_new(self, telegram_user: TelegramUser) -> bool:
        user_data = UserDTO(
            telegram_id=telegram_user.id,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            username=telegram_user.username,
        )
        async with self._uow:
            _, is_new = await self._uow.user.get_or_create(user_data)

        if is_new:
            logger.info(
                f"New user registered: {user_data.telegram_id} - {user_data.first_name} {user_data.last_name}"
            )


        return is_new
