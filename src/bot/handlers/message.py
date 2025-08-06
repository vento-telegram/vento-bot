import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dependency_injector.wiring import inject, Provide

from bot.container import Container
from bot.enums import BotModeEnum
from bot.interfaces.services.gpt import AbcOpenAIService
from bot.keyboards.mode import mode_keyboard

logger = logging.getLogger(__name__)

router = Router()

@router.message()
@inject
async def common_message_handler(
    message: Message,
    state: FSMContext,
    openai_service: AbcOpenAIService = Provide[Container.openai_service],
):
    logger.info(f"Message from user {message.from_user.id} {message.from_user.username}: {message.text}.")
    state_data = await state.get_data()
    mode = state_data.get("mode")

    if mode == BotModeEnum.chatgpt:
        status_msg = await message.answer("🔄 *Генерация ответа...*", parse_mode="Markdown")
        try:
            response = await openai_service.process_gpt_request(message, state)
            if response.image_url:
                await status_msg.edit_text(
                    f"🖼️ *Ваше изображение:*",
                    parse_mode="Markdown"
                )
                await message.answer_photo(response.image_url)
            else:
                await status_msg.edit_text(response.text, parse_mode="Markdown")
        except Exception as e:
            await status_msg.edit_text("❌ Произошла ошибка при генерации ответа.", parse_mode="Markdown")
            raise e
    elif mode == BotModeEnum.dalle:
        status_msg = await message.answer("🔄 *Генерация изображения...*", parse_mode="Markdown")
        response = await openai_service.process_dalle_request(message)
        await status_msg.edit_text(
            f"🖼️ *Ваше изображение:*",
            parse_mode="Markdown"
        )
        await message.answer_photo(response.image_url)
    elif mode == BotModeEnum.passive or not mode:
        await message.answer("👇 Сначала выбери, куда будем делать запрос:", reply_markup=mode_keyboard(BotModeEnum.passive))
