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
from bot.interfaces.services.pricing import AbcPricingService
from bot.keyboards.start import start_keyboard

logger = logging.getLogger(__name__)

router = Router()

@router.message(CommandStart())
@inject
async def start_handler(
    message: Message,
    state: FSMContext,
    user_service: AbcUserService = Provide[Container.user_service],
    pricing_service: AbcPricingService = Provide[Container.pricing_service],
):
    state_data = await state.get_data()
    user, is_new = await user_service.is_user_new(message.from_user)
    if is_new:
        await state.update_data(history=[], mode=BotModeEnum.passive)
        await message.answer(
            text=(
                "🎉 Добро пожаловать, я *Vento*!\n\n"
                "*Что я умею:*\n"
                "💬 Отвечаю на самые сложные вопросы с помощью GPT-5\n"
                "⚡ Быстрые и экономные ответы в режиме GPT-5 Mini\n"
                "🎨 Генерирую и редактирую изображения через DALL·E 3 и GPT Image\n"
                "🎬 Создаю видео с помощью Veo-3\n\n"
                "🎁 Тебе уже начислено 200 стартовых токенов — можно сразу начать!\n"
                "Если что, команда /start всегда поможет."
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
    current_mode = state_data.get('mode', BotModeEnum.passive)
    price = await pricing_service.get_price_for_mode(current_mode)
    await message.answer(
        text=(
            f"👋 Привет, *{message.from_user.first_name}*!\n\n"
            f"🪙 Твой баланс: *{user.balance}* токенов\n\n"
            f"🤖 Текущий ИИ: *{current_mode}*\n"
            f"💸 Цена запроса: *{price} токенов*\n\n"
            f"👇 Что хочешь сделать?"
        ),
        reply_markup=start_keyboard(current_mode, is_admin=bool(user.is_admin)),
        parse_mode=ParseMode.MARKDOWN,
    )
