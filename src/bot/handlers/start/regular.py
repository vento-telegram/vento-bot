import logging

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import CommandStart
from dependency_injector.wiring import inject, Provide

from bot.container import Container
from bot.enums import BotModeEnum
from bot.interfaces.services.user import AbcUserService
from bot.keyboards.start import start_keyboard

logger = logging.getLogger(__name__)

router = Router()

@router.message(CommandStart())
@inject
async def start_handler(
    message: Message,
    state: FSMContext,
    service: AbcUserService = Provide[Container.user_service],
):
    await state.update_data(history=[], mode=BotModeEnum.passive)
    state_data = await state.get_data()
    user, is_new = await service.is_user_new(message.from_user)
    if is_new:
        await message.answer(
            text=(
                "🎉 Добро пожаловать, я *Vento*!\n\n"
                "*Что я умею:*\n"
                "— 💬 Отвечаю на самые сложные вопросы с помощью GPT-5\n"
                "— 🎨 Генерирую изображения через DALL·E 3\n\n"
                "🎁 Тебе уже начислены стартовые токены — можно сразу начать!\n"
                "Если что, команда /start всегда поможет."
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
    await message.answer(
        text=f"👋 Привет, *{message.from_user.first_name}*!\n\n"
             f"🪙 Твой баланс: *{user.tokens} токенов*\n\n"
             f"🤖 Текущий ИИ: *{state_data.get('mode')}*\n"
             f"💸 Цена за запрос: *5 токенов*\n\n"
             f"👇 Что хочешь сделать?",
        reply_markup=start_keyboard(state_data.get('mode', BotModeEnum.passive)),
        parse_mode=ParseMode.MARKDOWN,
    )
