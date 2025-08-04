import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import CommandStart
from dependency_injector.wiring import inject, Provide

from bot.container import Container
from bot.enums import BotModeEnum
from bot.interfaces.services.user import AbcUserService
from bot.keyboards.mode import mode_keyboard

logger = logging.getLogger(__name__)

router = Router()

@router.message(CommandStart())
@inject
async def start_handler(
    message: Message,
    state: FSMContext,
    service: AbcUserService = Provide[Container.user_service],
):
    await state.update_data(mode=BotModeEnum.passive)
    text = await service.get_start_message(message.from_user)
    await message.answer(text, reply_markup=mode_keyboard(BotModeEnum.passive), parse_mode="Markdown")
