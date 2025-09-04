import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dependency_injector.wiring import inject, Provide

from bot.container import Container
from bot.enums import BotModeEnum
from bot.errors import OpenAIBadRequestError, InsufficientBalanceError
from bot.interfaces.services.gpt import AbcOpenAIService
from bot.interfaces.services.veo import AbcVeoService
from bot.interfaces.services.user import AbcUserService
from bot.interfaces.services.pricing import AbcPricingService
from bot.keyboards.change_ai import mode_keyboard
from bot.utils.telegram_format import prepare_telegram_messages_from_markdown

logger = logging.getLogger(__name__)

router = Router()

@router.message()
@inject
async def common_message_handler(
    message: Message,
    state: FSMContext,
    openai_service: AbcOpenAIService = Provide[Container.openai_service],
    user_service: AbcUserService = Provide[Container.user_service],
    pricing_service: AbcPricingService = Provide[Container.pricing_service],
):
    state_data = await state.get_data()
    mode = state_data.get("mode")
    user = await user_service.get_user(message.from_user.id)

    if user and getattr(user, "is_blocked", False):
        await message.answer("🚫 Ваш аккаунт заблокирован. Обратитесь в поддержку.")
        return

    if mode == BotModeEnum.gpt5:
        status_msg = await message.answer("🔄 *Генерация ответа...*", parse_mode="Markdown")
        try:
            response = await openai_service.process_gpt_request(message, state, user)
            parts = prepare_telegram_messages_from_markdown(response.text or "")
            if parts:
                await status_msg.edit_text(parts[0], parse_mode="Markdown")
                for extra in parts[1:]:
                    await message.answer(extra, parse_mode="Markdown")
        except InsufficientBalanceError:
            await status_msg.edit_text("❗️ *☹️ Недостаточно токенов для запроса*\nПополни баланс или попробуй позже.", parse_mode="Markdown")
        except OpenAIBadRequestError:
            await status_msg.edit_text("❗️ *☹️ OpenAI отклонил твой запрос*\nПожалуйста, попробуй изменить его.", parse_mode="Markdown")

    elif mode == BotModeEnum.gpt5_mini:
        status_msg = await message.answer("🔄 *Генерация ответа...*", parse_mode="Markdown")
        try:
            response = await openai_service.process_gpt_request(message, state)
            parts = prepare_telegram_messages_from_markdown(response.text or "")
            if parts:
                await status_msg.edit_text(parts[0], parse_mode="Markdown")
                for extra in parts[1:]:
                    await message.answer(extra, parse_mode="Markdown")
        except InsufficientBalanceError:
            await status_msg.edit_text("*☹️ Недостаточно токенов для запроса*\nПополни баланс или попробуй позже.", parse_mode="Markdown")
        except OpenAIBadRequestError:
            await status_msg.edit_text("*☹️ OpenAI отклонил твой запрос*\nПожалуйста, попробуй изменить его.", parse_mode="Markdown")

    elif mode == BotModeEnum.dalle3:
        status_msg = await message.answer("🔄 *Генерация изображения...*", parse_mode="Markdown")
        try:
            response = await openai_service.process_dalle_request(message)
            await message.answer_photo(response.image_url, caption="🖼️ Вот твоё изображение\n\n[Сделано в Vento](https://t.me/vento_toolbot)", parse_mode="Markdown")
        except InsufficientBalanceError:
            await status_msg.edit_text("*☹️ Недостаточно токенов для генерации изображения*\nПополни баланс или попробуй позже.", parse_mode="Markdown")
        except OpenAIBadRequestError:
            await status_msg.edit_text("*☹️ OpenAI отклонил твой запрос*\nПожалуйста, попробуй изменить или уточнить его.", parse_mode="Markdown")

    elif mode == BotModeEnum.passive or not mode:
        can_gpt5 = await pricing_service.ensure_user_can_afford(user.balance, BotModeEnum.gpt5)
        await message.answer(
            "👇 Сначала выбери, куда будем делать запрос:",
            reply_markup=mode_keyboard(BotModeEnum.passive, gpt5_available=can_gpt5),
        )
