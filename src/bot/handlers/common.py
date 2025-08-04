from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from dependency_injector.wiring import inject, Provide

from bot.di.container import Container
from bot.interfaces.services.user import AbstractUserService
from bot.keyboards.mode import mode_keyboard

router = Router()

@router.message(CommandStart())
@inject
async def start_handler(
    message: Message,
    service: AbstractUserService = Provide[Container.user_service],
):
    text = await service.get_start_message(message.from_user)
    await message.answer(text, reply_markup=mode_keyboard, parse_mode="Markdown")
