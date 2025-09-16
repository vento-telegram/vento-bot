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
from bot.interfaces.services.veo import AbcVeoService
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
    veo_service: AbcVeoService = Provide[Container.veo_service],
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

    elif mode == BotModeEnum.veo_video:
        text = (message.text or "").strip()
        state_data = await state.get_data()
        if not text:
            await message.answer("✍️ Пришли промпт на английском (можно добавить 1 изображение как ссылку в тексте)")
            return
        image_urls: list[str] = []
        for token in text.split():
            if token.startswith("http://") or token.startswith("https://"):
                image_urls.append(token)
                break
        prompt = text
        aspect = state_data.get("veo_aspect", "16:9")
        quality = state_data.get("veo_quality", "standard")
        enable_fallback = True if aspect == "16:9" else False
        watermark = None
        try:
            await veo_service.submit_veo_request(
                message,
                state,
                user,
                prompt=prompt,
                image_urls=image_urls or None,
                aspect_ratio=aspect,
                quality=quality,
                enable_fallback=enable_fallback,
                watermark=watermark,
            )
        except InsufficientBalanceError:
            await message.answer(
                "*☹️ Недостаточно токенов*\n\nПополните баланс или выберите стандартное качество.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="goto:account"),
                            InlineKeyboardButton(text="👾 Сменить модель", callback_data="goto:replenish"),
                        ]
                    ]
                ),
            )
            return

        if not text:
            await message.answer("✍️ Пришли промпт — текст песни/описание для трека.", reply_markup=suno_prompt_keyboard())
            return
        style = state_data.get("suno_style")
        if not style:
            await state.update_data(suno_style_pending=True)
            await message.answer("🧑‍🎤 Напиши стиль (жанры/описание), например: 'Быстрый эпичный рок'")
            return
        instrumental = state_data.get("suno_instrumental")
        if instrumental is None:
            # Ask to choose vocals before submitting
            await message.answer(
                "Добавить вокал?",
                reply_markup=suno_vocals_keyboard(),
            )
            return
        custom_mode = state_data.get("suno_custom_mode")
        if custom_mode is None:
            await message.answer(
                "Хочешь добавить свой текст или просто описать песню?",
                reply_markup=suno_input_mode_keyboard(),
            )
            return
        try:
            await suno_service.submit_suno_request(
                message,
                state,
                user,
                style=style,
                prompt=text,
                instrumental=instrumental,
                custom_mode=bool(custom_mode),
            )
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
