import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from dependency_injector.wiring import inject, Provide

from bot.container import Container
from bot.enums import BotModeEnum
from bot.errors import OpenAIBadRequestError, InsufficientBalanceError
from bot.interfaces.services.gpt import AbcOpenAIService
from bot.interfaces.services.user import AbcUserService
from bot.interfaces.services.suno import AbcSunoService
from bot.keyboards.change_ai import mode_keyboard
from bot.keyboards.suno import suno_styles_keyboard, suno_prompt_keyboard, suno_back_keyboard, suno_vocals_keyboard
from bot.utils.telegram_format import prepare_telegram_messages_from_markdown

logger = logging.getLogger(__name__)

router = Router()

@router.message()
@inject
async def common_message_handler(
    message: Message,
    state: FSMContext,
    openai_service: AbcOpenAIService = Provide[Container.openai_service],
    suno_service: AbcSunoService = Provide[Container.suno_service],
    user_service: AbcUserService = Provide[Container.user_service],
):
    state_data = await state.get_data()
    mode = state_data.get("mode")
    user = await user_service.get_user(message.from_user.id)

    if user.is_blocked:
        await message.answer("🚫 Ваш аккаунт заблокирован. Обратитесь в поддержку.")
        return

    if mode == BotModeEnum.gpt or mode == BotModeEnum.gpt_mini:
        status_msg = await message.answer("✨ *Готовлю ответ...*")
        try:
            response = await openai_service.process_gpt_request(message, state, user)
            parts = prepare_telegram_messages_from_markdown(response.text or "")
            if parts:
                await status_msg.edit_text(parts[0])
                for extra in parts[1:]:
                    await message.answer(extra)
        except InsufficientBalanceError:
            await status_msg.edit_text(
                "*☹️ Недостаточно токенов*\n\nТы можешь пополнить баланс токенов, оформить подписку на модель или выбрать более экономичную модель.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="goto:account"),
                            InlineKeyboardButton(text="👾 Сменить модель", callback_data="goto:replenish"),
                        ]
                    ]
                ),
            )
        except OpenAIBadRequestError:
            await status_msg.edit_text("*☹️ OpenAI отклонил твой запрос*\n\nПожалуйста, попробуй изменить его.")

    elif mode == BotModeEnum.gpt_image:
        try:
            await openai_service.submit_gpt_image_request(message, state, user)
        except InsufficientBalanceError:
            await message.answer(
                "*☹️ Недостаточно токенов*\n\nДля генерации изображения пополни баланс или выбери другую модель.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="goto:account"),
                            InlineKeyboardButton(text="👾 Сменить модель", callback_data="goto:replenish"),
                        ]
                    ]
                ),
            )

    elif mode == BotModeEnum.nano_banana:
        try:
            await openai_service.submit_nano_banana_request(message, state, user)
        except InsufficientBalanceError:
            await message.answer(
                "*☹️ Недостаточно токенов*\n\nПополните баланс или выберите другую модель.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="goto:account"),
                            InlineKeyboardButton(text="👾 Сменить модель", callback_data="goto:replenish"),
                        ]
                    ]
                ),
            )

    elif mode == BotModeEnum.suno_music:
        text = (message.text or "").strip()
        state_data = await state.get_data()
        pending_custom = state_data.get("suno_style_pending")
        if pending_custom and text:
            # Treat this message as custom style input
            await state.update_data(suno_style=text, suno_style_pending=False)
            await message.answer(
                f"🎼 Стиль выбран: *{text}*\n\nДобавить вокал?",
                reply_markup=suno_vocals_keyboard(),
            )
            return

        if not text:
            await message.answer("✍️ Пришли промпт — текст песни/описание для трека.", reply_markup=suno_prompt_keyboard())
            return
        style = state_data.get("suno_style")
        if not style:
            await message.answer("Сначала выбери стиль:", reply_markup=suno_styles_keyboard())
            return
        instrumental = state_data.get("suno_instrumental")
        if instrumental is None:
            # Ask to choose vocals before submitting
            await message.answer(
                "Добавить вокал?",
                reply_markup=suno_vocals_keyboard(),
            )
            return
        try:
            await suno_service.submit_suno_request(message, state, user, style=style, prompt=text, instrumental=instrumental)
        except InsufficientBalanceError:
            await message.answer(
                "*☹️ Недостаточно токенов*\n\nПополните баланс или выберите другую модель.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="goto:account"),
                            InlineKeyboardButton(text="👾 Сменить модель", callback_data="goto:replenish"),
                        ]
                    ]
                ),
            )

    elif mode == BotModeEnum.passive or not mode:
        await message.answer(
            "👇 Сначала выбери, куда будем делать запрос:",
            reply_markup=mode_keyboard(BotModeEnum.passive),
        )
