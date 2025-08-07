import logging

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import CommandStart
from dependency_injector.wiring import inject, Provide

from bot.container import Container
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
    await state.update_data(history=[])
    is_new = await service.is_user_new(message.from_user)
    if is_new:
        pass
    await message.answer(
        text=f"👋 Привет, *{message.from_user.first_name}*!\n\n"
             f"🪙 Твой баланс: *200 токенов*\n\n"
             f"🤖 Текущий ИИ: *GPT-4.5*\n"
             f"💸 Цена за запрос: *5 токенов*\n\n"
             f"👇 Что хочешь сделать?",
        reply_markup=start_keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )
