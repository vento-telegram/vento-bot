import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dependency_injector.wiring import inject, Provide

from bot.container import Container
from bot.enums import BotModeEnum
from bot.errors import OpenAIBadRequestError
from bot.interfaces.services.gpt import AbcOpenAIService
from bot.keyboards.change_ai import mode_keyboard

logger = logging.getLogger(__name__)

router = Router()

@router.message()
@inject
async def common_message_handler(
    message: Message,
    state: FSMContext,
    openai_service: AbcOpenAIService = Provide[Container.openai_service],
):
    # Кейсы
    # 1. Сообщение без контекста (пользователь не выбрал режим)
    # 2. Сообщение в режиме GPT
    # 2.1 Обычное сообщение только с текстом
    # 2.2 Сообщение только с текстом на генерацию изображения
    # 2.3 Сообщение только с фото
    # 2.4 Обычное сообщение только с голосовым сообщением
    # 2.5 Сообщение только с голосовым сообщением на генерацию изображения
    # 2.6 Сообщение с текстом и фото
    logger.info(f"Message from user {message.from_user.id} {message.from_user.username}: {message.text}.")
    state_data = await state.get_data()
    mode = state_data.get("mode")

    if mode == BotModeEnum.gpt5:
        status_msg = await message.answer("🔄 *Генерация ответа...*", parse_mode="Markdown")
        try:
            response = await openai_service.process_gpt_request(message, state)
            if response.image_url:
                await message.answer_photo(response.image_url, caption="🖼️ Вот твоё изображение\n\n[Сделано в Vento](https://t.me/vento_toolbot)", parse_mode="Markdown")
            else:
                await status_msg.edit_text(response.text, parse_mode="Markdown")
        except OpenAIBadRequestError:
            await status_msg.edit_text("❗️ *OpenAI отклонил твой запрос :(*\nПожалуйста, попробуй изменить его.", parse_mode="Markdown")

    elif mode == BotModeEnum.dalle3:
        status_msg = await message.answer("🔄 *Генерация изображения...*", parse_mode="Markdown")
        try:
            response = await openai_service.process_dalle_request(message)
            await message.answer_photo(response.image_url, caption="🖼️ Вот твоё изображение\n\n[Сделано в Vento](https://t.me/vento_toolbot)", parse_mode="Markdown")
        except OpenAIBadRequestError:
            await status_msg.edit_text("❗️ *К сожалению, OpenAI отклонил ваш запрос*\nПожалуйста, попробуйте изменить его.", parse_mode="Markdown")

    elif mode == BotModeEnum.passive or not mode:
        await message.answer("👇 Сначала выбери, куда будем делать запрос:", reply_markup=mode_keyboard(BotModeEnum.passive))
