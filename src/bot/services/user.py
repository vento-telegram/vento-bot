from bot.entities.user import UserDTO
from bot.interfaces.services.user import AbstractUserService
from bot.interfaces.uow import AbcUnitOfWork
from aiogram.types import User as TelegramUser


class UserService(AbstractUserService):
    def __init__(self, uow: AbcUnitOfWork):
        self._uow = uow

    async def get_start_message(self, telegram_user: TelegramUser):
        user_data = UserDTO(
            telegram_id=telegram_user.id,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            username=telegram_user.username,
        )
        async with self._uow:
            user, is_new = await self._uow.user.get_or_create(user_data)

        if is_new:
            text = (
                f"👋 Привет, *{user.first_name}*!\n\n"
                "Ты в *Vento AI* — помощнике на базе ChatGPT.\n\n"
                "🔮 Я умею:\n"
                "• 📟 GPT-4 диалоги\n"
                "• 🧠 Контекстный чат\n\n"
                "⚙️ В будущем появятся:\n"
                "• 🎞️ Veo-3 (видео)\n"
                "• 📚 Обработка документов\n\n"
                "👇 Выбери режим:"
            )
        else:
            text = (
                f"👋 С возвращением, *{user.first_name}*!\n\n"
                "👇 Выбери режим, с которого хочешь продолжить:"
            )

        return text



    # if is_new:
    #     text = (
    #         f"👋 Привет, *{message.from_user.first_name}*!\n\n"
    #         "Ты в *Vento AI* — помощнике на базе ChatGPT.\n\n"
    #         "🔮 Я умею:\n"
    #         "• 📟 GPT-4 диалоги\n"
    #         "• 🧠 Контекстный чат\n\n"
    #         "⚙️ В будущем появятся:\n"
    #         "• 🎞️ Veo-3 (видео)\n"
    #         "• 📚 Обработка документов\n\n"
    #         "👇 Выбери режим:"
    #     )
    # else:
    #     text = (
    #         f"👋 С возвращением, *{message.from_user.first_name}*!\n\n"
    #         "👇 Выбери режим, с которого хочешь продолжить:"
    #     )