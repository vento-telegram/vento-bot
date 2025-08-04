import logging

from bot.entities.user import UserDTO
from bot.interfaces.services.user import AbcUserService
from bot.interfaces.uow import AbcUnitOfWork
from aiogram.types import User as TelegramUser

logger = logging.getLogger(__name__)

class UserService(AbcUserService):
    def __init__(self, uow: AbcUnitOfWork):
        self._uow = uow

    async def get_start_message(self, telegram_user: TelegramUser) -> str:
        user_data = UserDTO(
            telegram_id=telegram_user.id,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            username=telegram_user.username,
        )
        async with self._uow:
            user, is_new = await self._uow.user.get_or_create(user_data)

        if is_new:
            logger.info(f"New user added to database: ID: {user.telegram_id} Username: {user.username}")
            return (
                f"👋 Привет, *{user.first_name}*!\n\n"
                "Я — *Vento AI*, твой персональный ИИ-мультитул.\n\n"
                "🔮 Я умею:\n"
                "• 📟 GPT-4 диалоги\n"
                "• 🧠 Контекстный чат\n\n"
                "⚙️ В будущем появятся:\n"
                "• 🎞️ Veo-3 (видео)\n"
                "• 📚 Обработка документов\n\n"
                "👇 Выбери, в каком режиме будем работать:"
            )
        return  (
            f"👋 Привет, *{user.first_name}*!\n\n"
            "👇 Выбери режим, в котором будем работать:"
        )
