import logging

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import CommandStart
from dependency_injector.wiring import inject, Provide
from sqlalchemy.orm import mapper

from bot.constants import settings_models_mapper
from bot.container import Container
from bot.enums import BotModeEnum
from bot.interfaces.services.user import AbcUserService
from bot.interfaces.services.settings import AbcSettingsService
from bot.keyboards.start import start_keyboard

logger = logging.getLogger(__name__)

router = Router()

@router.message(CommandStart())
@inject
async def start_handler(
    message: Message,
    state: FSMContext,
    user_service: AbcUserService = Provide[Container.user_service],
    settings_service: AbcSettingsService = Provide[Container.settings_service],
):
    state_data = await state.get_data()
    user, is_new = await user_service.is_user_new(message.from_user)
    if is_new:
        await state.update_data(history=[], mode=BotModeEnum.passive)
        start_bonus = await settings_service.get_value("start_bonus")
        await message.answer(
            text=(
                "🎉 Добро пожаловать, я *Vento*!\n\n"
                "*Что я умею:*\n"
                "💬 Отвечаю на самые сложные вопросы с помощью *GPT-5*\n"
                "⚡ Быстрые и экономные ответы в режиме *GPT-5 Mini*\n\n"
                f"🎁 Тебе уже начислено *{start_bonus}* стартовых токенов — можно сразу начать!\n"
                "Если что, команда /start всегда поможет."
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
    current_mode = state_data.get('mode', BotModeEnum.passive)

    text = (
        f"👋 Привет, *{message.from_user.first_name}*!\n\n"
        f"🪙 Твой баланс: *{user.balance}* токенов\n\n"
        f"🤖 Текущий ИИ: *{current_mode}*\n"
    )

    if current_mode != BotModeEnum.passive:
        price = await settings_service.get_value(settings_models_mapper[current_mode])
        text += f"💸 Цена запроса: *{price} токенов*\n\n"
    else:
        text += "\n"

    text += "👇 Что хочешь сделать?"

    await message.answer(
        text=text,
        reply_markup=start_keyboard(current_mode, is_admin=bool(user.is_admin)),
        parse_mode=ParseMode.MARKDOWN,
    )
