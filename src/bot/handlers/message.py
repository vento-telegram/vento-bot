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
from bot.keyboards.suno import (
    suno_styles_keyboard,
    suno_prompt_keyboard,
    suno_back_keyboard,
    suno_vocals_keyboard,
    suno_input_mode_keyboard,
    suno_main_settings_keyboard,
)
from bot.utils.telegram_format import prepare_telegram_messages_from_markdown
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)

router = Router()


async def _get_telegram_file_url(bot, file_id: str) -> str:
    file = await bot.get_file(file_id)
    return f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"

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
        # Validate input type and size before calling GPT
        MAX_FILE_SIZE_MB = 20
        def _file_too_large(size_bytes: int | None) -> bool:
            try:
                return bool(size_bytes and size_bytes > MAX_FILE_SIZE_MB * 1024 * 1024)
            except Exception:
                return False

        # Disallow unsupported content types
        doc_mime = (message.document.mime_type or "").lower() if message.document else ""
        if any([
            message.video,
            message.animation,
            message.audio,
            # message.voice is allowed
            message.video_note,
            message.sticker,
            message.location,
            message.venue if hasattr(message, 'venue') else False,
            message.contact,
            message.poll,
            message.dice,
            (message.document and not doc_mime.startswith("image/")),  # только изображения-документы разрешены
        ]):
            await message.answer(
                (
                    "☹️ Этот тип сообщения не поддерживается.\n\n"
                    "Допустимые варианты:\n"
                    "• текст\n"
                    "• фото (с подписью или без)\n"
                    "• изображение как документ (JPEG/PNG/WebP и т.п.)\n"
                    "• голосовое сообщение\n\n"
                    f"Макс. размер фото/изображения: {MAX_FILE_SIZE_MB} МБ. Если больше — сожмите или уменьшите разрешение."
                )
            )
            return

        # Size checks for photo/document
        if message.photo:
            try:
                photo = message.photo[-1]
                if _file_too_large(getattr(photo, 'file_size', None)):
                    size_mb = (getattr(photo, 'file_size', 0) or 0) / (1024 * 1024)
                    await message.answer(
                        (
                            f"☹️ Файл слишком большой: {size_mb:.1f} МБ.\n"
                            f"Максимум: {MAX_FILE_SIZE_MB} МБ.\n"
                            "Попробуйте уменьшить размер/разрешение, или пришлите ссылку на файл."
                        )
                    )
                    return
            except Exception:
                pass
        # Проверка размера для изображений-документов
        if message.document and doc_mime.startswith("image/"):
            try:
                if _file_too_large(getattr(message.document, 'file_size', None)):
                    size_mb = (getattr(message.document, 'file_size', 0) or 0) / (1024 * 1024)
                    await message.answer(
                        (
                            f"☹️ Файл слишком большой: {size_mb:.1f} МБ.\n"
                            f"Максимум: {MAX_FILE_SIZE_MB} МБ.\n"
                            "Попробуйте уменьшить размер/разрешение."
                        )
                    )
                    return
            except Exception:
                pass

        status_msg = await message.answer("✨ *Готовлю ответ...*")
        try:
            response = await openai_service.process_gpt_request(message, state, user)
            raw_text = response.text or ""
            logger.debug("GPT raw len=%d snippet=%r", len(raw_text), raw_text[:400])
            parts = prepare_telegram_messages_from_markdown(raw_text)
            logger.debug("Telegram parts: count=%d lens=%s", len(parts), [len(p) for p in parts])
            if parts:
                try:
                    await status_msg.edit_text(parts[0])
                except TelegramBadRequest as e:
                    logger.exception("edit_text markdown error on part=0 len=%d: %s", len(parts[0]), str(e))
                    try:
                        await status_msg.edit_text(parts[0], parse_mode=None)
                    except Exception:
                        logger.exception("edit_text fallback failed")
                for idx, extra in enumerate(parts[1:], start=1):
                    try:
                        await message.answer(extra)
                    except TelegramBadRequest as e:
                        logger.exception("answer markdown error on part=%d len=%d: %s", idx, len(extra), str(e))
                        try:
                            await message.answer(extra, parse_mode=None)
                        except Exception:
                            logger.exception("answer fallback failed for part=%d", idx)
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
            # Treat this message as custom style input and return to Suno main menu
            await state.update_data(suno_style=text, suno_style_pending=False)
            data = await state.get_data()
            await message.answer(
                "🎵 Выбери настройки генерации музыкальной композиции (стиль, вокал, режим ввода).\n\n"
                "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужной композиции или текстом.\n\n"
                "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start",
                reply_markup=suno_main_settings_keyboard(
                    data.get("suno_style"),
                    data.get("suno_instrumental"),
                    data.get("suno_custom_mode"),
                ),
            )
            return

        # Validate settings completeness before accepting prompt
        style = state_data.get("suno_style")
        instrumental = state_data.get("suno_instrumental")
        custom_mode = state_data.get("suno_custom_mode")

        need_input_mode = (instrumental is False)
        settings_complete = bool(style) and (instrumental is not None) and (not need_input_mode or (custom_mode is not None))

        if not settings_complete:
            # Ensure we are not expecting free-text style right now
            try:
                await state.update_data(suno_style_pending=False)
            except Exception:
                pass
            # Block prompt until settings are filled
            await message.answer(
                "✋ Сначала укажи необходимые тебе настройки с помощью кнопок в сообщении выше, затем отправь запрос с описанием нужной композиции или её текстом.",
            )
            return

        if not text:
            await message.answer("✍️ Пришли промпт — текст песни/описание для трека.", reply_markup=suno_prompt_keyboard())
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
            return

    elif mode == BotModeEnum.veo_video:
        state_data = await state.get_data()
        aspect = state_data.get("veo_aspect")
        quality = state_data.get("veo_quality")

        # Collect image (photo or image document) if provided
        image_urls: list[str] = []
        prompt: str = ""

        if message.photo:
            # Use the largest available size
            try:
                url = await _get_telegram_file_url(message.bot, message.photo[-1].file_id)
                image_urls = [url]
            except Exception:
                image_urls = []
            prompt = (message.caption or "").strip()
        elif message.document and (message.document.mime_type or "").lower().startswith("image/"):
            try:
                url = await _get_telegram_file_url(message.bot, message.document.file_id)
                image_urls = [url]
            except Exception:
                image_urls = []
            prompt = (message.caption or "").strip()
        else:
            # Text-to-video path (optionally containing one image URL)
            text = (message.text or "").strip()
            if not text:
                await message.answer("✍️ Пришли промпт на английском или фото с подписью (1 изображение)")
                return
            for token in text.split():
                if token.startswith("http://") or token.startswith("https://"):
                    image_urls.append(token)
                    break
            prompt = text

        # Default prompt for image-only messages
        if not prompt:
            prompt = "Animate this image into a short cinematic video with smooth motion."

        if not aspect or not quality:
            await message.answer(
                "✋ Сначала выбери формат и качество в сообщении выше, затем отправь запрос.",
            )
            return

        enable_fallback = True if aspect == "16:9" else False
        watermark = None
        try:
            # Conservative translation step via gpt-5-mini
            if prompt:
                try:
                    prompt = await openai_service.translate_for_veo(prompt)
                except Exception:
                    pass
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


    elif mode == BotModeEnum.passive or not mode:
        await message.answer(
            "👇 Сначала выбери, куда будем делать запрос:",
            reply_markup=mode_keyboard(BotModeEnum.passive),
        )
