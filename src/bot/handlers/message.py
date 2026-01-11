import asyncio
import logging

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from dependency_injector.wiring import Provide, inject

from bot.container import Container
from bot.enums import BotModeEnum
from bot.errors import InsufficientBalanceError, OpenAIBadRequestError
from bot.interfaces.services.gpt import AbcOpenAIService
from bot.interfaces.services.suno import AbcSunoService
from bot.interfaces.services.sora2 import AbcSora2Service
from bot.interfaces.services.sora2_pro import AbcSora2ProService
from bot.interfaces.services.user import AbcUserService
from bot.interfaces.services.veo import AbcVeoService
from bot.keyboards.change_ai import mode_keyboard
from bot.keyboards.sora2 import sora2_aspect_keyboard
from bot.keyboards.sora2_pro import (
    sora2pro_aspect_keyboard,
    sora2pro_duration_keyboard,
)
from bot.keyboards.suno import (
    suno_main_settings_keyboard,
    suno_prompt_keyboard,
)
from bot.keyboards.nano import nano_main_settings_keyboard
from bot.keyboards.nano_pro import nano_pro_main_settings_keyboard
from bot.utils.mode import normalize_mode
from bot.utils.telegram_format import prepare_telegram_messages_from_markdown
from bot.settings import settings

logger = logging.getLogger(__name__)

router = Router()

# State holders for Sora media groups (albums)
SORA_GROUP_LOCKS: dict[str, asyncio.Lock] = {}
SORA_MEDIA_GROUPS: dict[str, dict] = {}
SORA_MEDIA_GROUP_QUIET_SECONDS = 0.6


async def _run_sora2_request(
    message: Message,
    state: FSMContext,
    user,
    prompt: str,
    image_urls: list[str] | None,
    aspect: str,
    sora2_service: AbcSora2Service,
) -> None:
    status_msg = await message.answer(
        "🎬 *Работаю над видео...*\n\n"
        "Я пришлю результат, как только он будет готов. Это может занять несколько минут."
    )
    try:
        await sora2_service.submit_sora2_request(
            message,
            state,
            user,
            prompt=prompt,
            image_urls=image_urls or None,
            aspect_ratio=aspect,
        )
    except InsufficientBalanceError:
        try:
            await status_msg.edit_text(
                "*☹️ Недостаточно токенов*\n\nТы можешь пополнить баланс, выбрать другую модель или пригласить друга через реферальную программу и получить *бесплатные токены*.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="🎟️ Больше токенов", callback_data="goto:replenish"),
                        ],
                        [
                            InlineKeyboardButton(text="🔥 Реферальная программа", callback_data="goto:referral"),
                        ],
                        [
                            InlineKeyboardButton(text="👾 Сменить модель", callback_data="goto:switch"),
                        ],
                    ]
                ),
            )
        except Exception:
            await message.answer(
                "*☹️ Недостаточно токенов*\n\nТы можешь пополнить баланс, выбрать другую модель или пригласить друга через реферальную программу и получить *бесплатные токены*.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="🎟️ Больше токенов", callback_data="goto:replenish"),
                        ],
                        [
                            InlineKeyboardButton(text="🔥 Реферальная программа", callback_data="goto:referral"),
                        ],
                        [
                            InlineKeyboardButton(text="👾 Сменить модель", callback_data="goto:switch"),
                        ],
                    ]
                ),
            )
        return
    except Exception:
        logger.exception("Unexpected error in Sora2 handler")
        try:
            await status_msg.edit_text("Не удалось отправить запрос в Sora 2. Попробуй позже.")
        except Exception:
            try:
                await message.answer("Не удалось отправить запрос в Sora 2. Попробуй позже.")
            except Exception:
                pass


async def _run_sora2_pro_request(
    message: Message,
    state: FSMContext,
    user,
    prompt: str,
    image_urls: list[str] | None,
    aspect: str,
    n_frames: str,
    sora2_pro_service: AbcSora2ProService,
) -> None:
    status_msg = await message.answer(
        "🎥 *Работаю над видео...*\n\n"
        "Я пришлю результат, как только он будет готов. Это может занять несколько минут."
    )
    try:
        await sora2_pro_service.submit_sora2_pro_request(
            message,
            state,
            user,
            prompt=prompt,
            image_urls=image_urls or None,
            aspect_ratio=aspect,
            n_frames=n_frames,
        )
    except InsufficientBalanceError:
        try:
            await status_msg.edit_text(
                "*☹️ Недостаточно токенов*\n\nТы можешь пополнить баланс, выбрать другую модель или пригласить друга через реферальную программу и получить *бесплатные токены*.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="🎟️ Больше токенов", callback_data="goto:replenish"),
                        ],
                        [
                            InlineKeyboardButton(text="🔥 Реферальная программа", callback_data="goto:referral"),
                        ],
                        [
                            InlineKeyboardButton(text="👾 Сменить модель", callback_data="goto:switch"),
                        ],
                    ]
                ),
            )
        except Exception:
            await message.answer(
                "*☹️ Недостаточно токенов*\n\nТы можешь пополнить баланс, выбрать другую модель или пригласить друга через реферальную программу и получить *бесплатные токены*.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="🎟️ Больше токенов", callback_data="goto:replenish"),
                        ],
                        [
                            InlineKeyboardButton(text="🔥 Реферальная программа", callback_data="goto:referral"),
                        ],
                        [
                            InlineKeyboardButton(text="👾 Сменить модель", callback_data="goto:switch"),
                        ],
                    ]
                ),
            )
        return
    except Exception:
        logger.exception("Unexpected error in Sora2 Pro handler")
        try:
            await status_msg.edit_text("Ошибка при отправке запроса в Sora 2 Pro. Напишите в поддержку.")
        except Exception:
            try:
                await message.answer("Ошибка при отправке запроса в Sora 2 Pro. Напишите в поддержку.")
            except Exception:
                pass


async def _finalize_sora_media_group_after_quiet_period(
    media_group_id: str,
    scheduled_expires_at: float,
    message: Message,
    state: FSMContext,
    user,
    mode: BotModeEnum,
    sora2_service: AbcSora2Service,
    sora2_pro_service: AbcSora2ProService,
) -> None:
    try:
        loop = asyncio.get_running_loop()
        delay = max(0.0, scheduled_expires_at - loop.time())
        if delay:
            await asyncio.sleep(delay)

        lock_key = f"{message.chat.id}:{media_group_id}:{mode.value}"
        data = await state.get_data()
        groups = dict(data.get("sora_media_groups") or {})
        group = groups.get(media_group_id) or SORA_MEDIA_GROUPS.get(lock_key)
        if not group:
            return
        if group.get("finalized"):
            return
        if float(group.get("expires_at") or 0.0) != float(scheduled_expires_at):
            return
        if group.get("mode") != mode.value:
            return

        file_ids = list(group.get("file_ids") or [])
        caption = (group.get("caption") or "").strip()

        # Cleanup state before heavy work to avoid double processing
        group["finalized"] = True
        groups.pop(media_group_id, None)
        SORA_MEDIA_GROUPS.pop(lock_key, None)
        await state.update_data(sora_media_groups=groups)

        if not caption:
            await message.answer("Добавь подпись к изображениям (текстовый запрос).")
            return

        image_urls: list[str] = []
        for fid in file_ids:
            try:
                url = await _get_telegram_file_url(message.bot, fid)
                if url:
                    image_urls.append(url)
            except Exception:
                logger.exception("Failed to get file URL for Sora media group item")

        if not image_urls:
            await message.answer("Не удалось получить изображения. Попробуй ещё раз.")
            return

        state_data = await state.get_data()
        if mode == BotModeEnum.sora2_video:
            aspect = state_data.get("sora_aspect")
            if not aspect:
                await message.answer("✋ Сначала выбери формат: 16:9 или 9:16", reply_markup=sora2_aspect_keyboard(aspect))
                return
            await _run_sora2_request(message, state, user, caption, image_urls, aspect, sora2_service)
        elif mode == BotModeEnum.sora2_pro_video:
            aspect = state_data.get("sora_pro_aspect")
            n_frames = state_data.get("sora_pro_frames")
            if not aspect:
                await message.answer("📐 Выбери соотношение сторон: 16:9 или 9:16", reply_markup=sora2pro_aspect_keyboard(aspect))
                return
            if n_frames not in {"10", "15"}:
                await message.answer("⏱️ Выбери длительность ролика: 10 или 15 сек", reply_markup=sora2pro_duration_keyboard(n_frames))
                return
            await _run_sora2_pro_request(message, state, user, caption, image_urls, aspect, n_frames, sora2_pro_service)
    except Exception:
        logger.exception("Failed to finalize Sora media group")


async def _handle_sora_media_group_item(
    message: Message,
    state: FSMContext,
    user,
    mode: BotModeEnum,
    sora2_service: AbcSora2Service,
    sora2_pro_service: AbcSora2ProService,
) -> bool:
    media_group_id_raw = message.media_group_id
    media_group_id = str(media_group_id_raw) if media_group_id_raw is not None else None
    has_image = bool(message.photo) or (message.document and (message.document.mime_type or "").lower().startswith("image/"))
    if not media_group_id or not has_image:
        return False

    loop = asyncio.get_running_loop()
    now = loop.time()
    quiet_seconds = SORA_MEDIA_GROUP_QUIET_SECONDS

    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document and (message.document.mime_type or "").lower().startswith("image/"):
        file_id = message.document.file_id
    else:
        return False

    lock_key = f"{message.chat.id}:{media_group_id}:{mode.value}"
    lock = SORA_GROUP_LOCKS.setdefault(lock_key, asyncio.Lock())
    async with lock:
        data = await state.get_data()
        groups = dict(data.get("sora_media_groups") or {})
        group = dict(groups.get(media_group_id) or SORA_MEDIA_GROUPS.get(lock_key) or {})

        file_ids = list(group.get("file_ids") or [])
        file_ids.append(file_id)

        existing_caption = (group.get("caption") or "").strip() or None
        incoming_caption = (message.caption or "").strip() or None
        caption = existing_caption or incoming_caption

        expires_at = now + quiet_seconds
        group.update(
            {
                "file_ids": file_ids,
                "caption": caption,
                "expires_at": expires_at,
                "finalized": False,
                "mode": mode.value,
            }
        )

        SORA_MEDIA_GROUPS[lock_key] = group
        groups[media_group_id] = group
        await state.update_data(sora_media_groups=groups)

    asyncio.create_task(
        _finalize_sora_media_group_after_quiet_period(
            media_group_id=media_group_id,
            scheduled_expires_at=expires_at,
            message=message,
            state=state,
            user=user,
            mode=mode,
            sora2_service=sora2_service,
            sora2_pro_service=sora2_pro_service,
        )
    )
    return True


async def _get_telegram_file_url(bot, file_id: str) -> str:
    file = await bot.get_file(file_id)
    return f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"

# Unified user-facing error message for model interaction failures
SUPPORT_ERROR_TEXT = (
    f"🚨 Произошла ошибка при взамодействии с моделью.\n\n"
    f"Свяжись с нашей поддержкой, чтобы получить помощь @{settings.SUPPORT_USERNAME}"
)

@router.message()
@inject
async def common_message_handler(
    message: Message,
    state: FSMContext,
    openai_service: AbcOpenAIService = Provide[Container.openai_service],
    suno_service: AbcSunoService = Provide[Container.suno_service],
    veo_service: AbcVeoService = Provide[Container.veo_service],
    sora2_service: AbcSora2Service = Provide[Container.sora2_service],
    sora2_pro_service: AbcSora2ProService = Provide[Container.sora2_pro_service],
    user_service: AbcUserService = Provide[Container.user_service],
):
    # Ignore slash-commands to avoid conflicts with command routers
    if (message.text or "").strip().startswith("/"):
        return
    state_data = await state.get_data()
    raw_mode = state_data.get("mode", BotModeEnum.passive)
    mode = normalize_mode(raw_mode)
    if raw_mode not in (None, "") and raw_mode != mode:
        await state.update_data(mode=mode)
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

        # Special-case unsupported image formats (e.g., HEIC/HEIF sent as a file)
        if message.document and doc_mime.startswith("image/"):
            allowed_mimes = {"image/jpeg", "image/png", "image/webp", "image/gif"}
            file_name = (message.document.file_name or "").lower()
            ext = file_name.rsplit(".", 1)[-1] if "." in file_name else ""
            if (doc_mime not in allowed_mimes) or (ext and ext not in {"jpg", "jpeg", "png", "webp", "gif"}):
                if "heic" in doc_mime or "heif" in doc_mime or ext in {"heic", "heif"}:
                    await message.answer("Этот формат изображения (HEIC/HEIF) не поддерживается моделью.\n\nПожалуйста, пришлите его как фото (не как файл) — Telegram автоматически конвертирует в JPEG.\nЛибо заранее конвертируйте в JPEG/PNG/WebP.")
                else:
                    await message.answer("Этот формат изображения не поддерживается моделью.\n\nОтправьте файл как фото (не как документ) — Telegram преобразует в совместимый JPEG, или конвертируйте изображение в JPEG/PNG/WebP.")
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
                    await status_msg.delete()
                except TelegramBadRequest:
                    # Message might already be gone (e.g., user deleted it) – ignore
                    pass
                except Exception:
                    logger.exception("Failed to delete GPT status message before sending reply")

                for idx, part in enumerate(parts):
                    try:
                        await message.answer(part)
                    except TelegramBadRequest as e:
                        logger.exception("answer markdown error on part=%d len=%d: %s", idx, len(part), str(e))
                        try:
                            await message.answer(part, parse_mode=None)
                        except Exception:
                            logger.exception("answer fallback failed for part=%d", idx)
        except InsufficientBalanceError:
            await status_msg.edit_text(
                "*☹️ Недостаточно токенов*\n\nТы можешь пополнить баланс, выбрать другую модель или пригласить друга через реферальную программу и получить *бесплатные токены*.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="🎟️ Больше токенов", callback_data="goto:replenish"),
                        ],
                        [
                            InlineKeyboardButton(text="🔥 Реферальная программа", callback_data="goto:referral"),
                        ],
                        [
                            InlineKeyboardButton(text="👾 Сменить модель", callback_data="goto:switch"),
                        ],
                    ]
                ),
            )
        except OpenAIBadRequestError:
            await status_msg.edit_text("*☹️ OpenAI отклонил твой запрос*\n\nПожалуйста, попробуй изменить его.")

    elif mode == BotModeEnum.nano_banana:
        state_data = await state.get_data()
        image_size = state_data.get("nano_format")
        if not image_size:
            await message.answer(
                "Сначала выбери формат изображения Nano Banana.",
                reply_markup=nano_main_settings_keyboard(image_size),
            )
            return
        try:
            await openai_service.submit_nano_banana_request(message, state, user, image_size)
        except InsufficientBalanceError:
            await message.answer(
                "*☹️ Недостаточно токенов*\n\nТы можешь пополнить баланс, выбрать другую модель или пригласить друга через реферальную программу и получить *бесплатные токены*.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="🎟️ Больше токенов", callback_data="goto:replenish"),
                        ],
                        [
                            InlineKeyboardButton(text="🔥 Реферальная программа", callback_data="goto:referral"),
                        ],
                        [
                            InlineKeyboardButton(text="👾 Сменить модель", callback_data="goto:switch"),
                        ],
                    ]
                ),
            )

        except Exception:
            logger.exception("Unexpected error in Nano Banana handler")
            await message.answer("Не удалось отправить запрос. Попробуйте ещё раз позже.")

    elif mode == BotModeEnum.nano_banana_pro:
        state_data = await state.get_data()
        image_size = state_data.get("nano_pro_format")
        if not image_size:
            await message.answer(
                "Сначала выбери формат изображения Nano Banana Pro.",
                reply_markup=nano_pro_main_settings_keyboard(image_size),
            )
            return
        try:
            await openai_service.submit_nano_banana_pro_request(message, state, user, image_size)
        except InsufficientBalanceError:
            await message.answer(
                "*☹️ Недостаточно токенов*\n\nТы можешь пополнить баланс, выбрать другую модель или пригласить друга через реферальную программу и получить *бесплатные токены*.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="🎟️ Больше токенов", callback_data="goto:replenish"),
                        ],
                        [
                            InlineKeyboardButton(text="🔥 Реферальная программа", callback_data="goto:referral"),
                        ],
                        [
                            InlineKeyboardButton(text="👾 Сменить модель", callback_data="goto:switch"),
                        ],
                    ]
                ),
            )

        except Exception:
            logger.exception("Unexpected error in Nano Banana Pro handler")
            await message.answer("Не удалось отправить запрос. Попробуйте ещё раз позже.")

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
                "*☹️ Недостаточно токенов*\n\nТы можешь пополнить баланс, выбрать другую модель или пригласить друга через реферальную программу и получить *бесплатные токены*.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="🎟️ Больше токенов", callback_data="goto:replenish"),
                        ],
                        [
                            InlineKeyboardButton(text="🔥 Реферальная программа", callback_data="goto:referral"),
                        ],
                        [
                            InlineKeyboardButton(text="👾 Сменить модель", callback_data="goto:switch"),
                        ],
                    ]
                ),
            )
            return

        except Exception:
            logger.exception("Unexpected error in Suno handler")
            await message.answer("Не удалось отправить запрос в Suno. Попробуйте ещё раз позже.")

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
            _cap = (message.caption or "").strip()
            prompt = _cap if _cap else "Animate this photo"
        elif message.document and (message.document.mime_type or "").lower().startswith("image/"):
            try:
                url = await _get_telegram_file_url(message.bot, message.document.file_id)
                image_urls = [url]
            except Exception:
                image_urls = []
            _cap = (message.caption or "").strip()
            prompt = _cap if _cap else "Animate this photo"
        else:
            # Text-to-video path (optionally containing one image URL)
            text = (message.text or "").strip()
            if not text:
                await message.answer("✍️ Пришли запрос текстом или фото с подписью (1 изображение)")
                return
            for token in text.split():
                if token.startswith("http://") or token.startswith("https://"):
                    image_urls.append(token)
                    break
            prompt = text

        # Default prompt for image-only messages
        if not prompt:
            prompt = "Animate this photo"

        if not aspect or not quality:
            await message.answer(
                "✋ Сначала выбери формат и качество в сообщении выше, затем отправь запрос.",
            )
            return

        enable_fallback = True if aspect == "16:9" else False
        watermark = None
        # Send immediate status message before translation and API call
        status_msg = await message.answer(
            "🎬 *Работаю над видео...*\n\n"
            "Я пришлю результат, как только он будет готов. Это может занять несколько минут."
        )
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
            try:
                await status_msg.edit_text(
                    "*☹️ Недостаточно токенов*\n\nТы можешь пополнить баланс, выбрать другую модель или пригласить друга через реферальную программу и получить *бесплатные токены*.",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(text="🎟️ Больше токенов", callback_data="goto:replenish"),
                            ],
                            [
                                InlineKeyboardButton(text="🔥 Реферальная программа", callback_data="goto:referral"),
                            ],
                            [
                                InlineKeyboardButton(text="👾 Сменить модель", callback_data="goto:switch"),
                            ],
                        ]
                    ),
                )
            except Exception:
                await message.answer(
                    "*☹️ Недостаточно токенов*\n\nТы можешь пополнить баланс, выбрать другую модель или пригласить друга через реферальную программу и получить *бесплатные токены*.",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(text="🎟️ Больше токенов", callback_data="goto:replenish"),
                            ],
                            [
                                InlineKeyboardButton(text="🔥 Реферальная программа", callback_data="goto:referral"),
                            ],
                            [
                                InlineKeyboardButton(text="👾 Сменить модель", callback_data="goto:switch"),
                            ],
                        ]
                    ),
                )
            return


        except Exception:
            logger.exception("Unexpected error in VEO handler")
            try:
                await status_msg.edit_text("Не удалось отправить запрос на генерацию видео. Попробуйте ещё раз позже.")
            except Exception:
                try:
                    await message.answer("Не удалось отправить запрос на генерацию видео. Попробуйте ещё раз позже.")
                except Exception:
                    pass

    elif mode == BotModeEnum.sora2_video:
        state_data = await state.get_data()

        aspect = state_data.get("sora_aspect")

        has_image = bool(message.photo) or (message.document and (message.document.mime_type or "").lower().startswith("image/"))
        # Collect media group items to allow multiple images (albums)
        handled_group = await _handle_sora_media_group_item(
            message=message,
            state=state,
            user=user,
            mode=BotModeEnum.sora2_video,
            sora2_service=sora2_service,
            sora2_pro_service=sora2_pro_service,
        )
        if handled_group:
            return

        image_urls: list[str] = []
        prompt: str = ""
        if has_image and message.photo:
            try:
                url = await _get_telegram_file_url(message.bot, message.photo[-1].file_id)
                image_urls = [url]
            except Exception:
                image_urls = []
            _cap = (message.caption or "").strip()
            if not _cap:
                await message.answer("Добавь описание к изображению (подпись)")
                return
            prompt = _cap
        elif has_image and message.document and (message.document.mime_type or "").lower().startswith("image/"):
            try:
                url = await _get_telegram_file_url(message.bot, message.document.file_id)
                image_urls = [url]
            except Exception:
                image_urls = []
            _cap = (message.caption or "").strip()
            if not _cap:
                await message.answer("Добавь описание к изображению")
                return
            prompt = _cap
        else:
            text = (message.text or "").strip()
            if not text:
                await message.answer("Пришли текст или одну/несколько картинок с описанием")
                return
            prompt = text

        if not aspect:
            await message.answer("✋ Сначала выбери формат: 16:9 или 9:16", reply_markup=sora2_aspect_keyboard(aspect))
            return

        await _run_sora2_request(
            message=message,
            state=state,
            user=user,
            prompt=prompt,
            image_urls=image_urls or None,
            aspect=aspect,
            sora2_service=sora2_service,
        )

    elif mode == BotModeEnum.sora2_pro_video:
        state_data = await state.get_data()

        aspect = state_data.get("sora_pro_aspect")
        n_frames = state_data.get("sora_pro_frames")

        has_image = bool(message.photo) or (message.document and (message.document.mime_type or "").lower().startswith("image/"))
        handled_group = await _handle_sora_media_group_item(
            message=message,
            state=state,
            user=user,
            mode=BotModeEnum.sora2_pro_video,
            sora2_service=sora2_service,
            sora2_pro_service=sora2_pro_service,
        )
        if handled_group:
            return

        image_urls: list[str] = []
        prompt: str = ""
        if has_image and message.photo:
            try:
                url = await _get_telegram_file_url(message.bot, message.photo[-1].file_id)
                image_urls = [url]
            except Exception:
                image_urls = []
            _cap = (message.caption or "").strip()
            if not _cap:
                await message.answer("Добавьте подпись к изображению (текстовый запрос)")
                return
            prompt = _cap
        elif has_image and message.document and (message.document.mime_type or "").lower().startswith("image/"):
            try:
                url = await _get_telegram_file_url(message.bot, message.document.file_id)
                image_urls = [url]
            except Exception:
                image_urls = []
            _cap = (message.caption or "").strip()
            if not _cap:
                await message.answer("Добавьте подпись к изображению (текстовый запрос)")
                return
            prompt = _cap
        else:
            text = (message.text or "").strip()
            if not text:
                await message.answer("Пришлите текст запроса или одно/несколько изображений с подписью")
                return
            prompt = text

        if not aspect:
            await message.answer("📐 Выбери соотношение сторон: 16:9 или 9:16", reply_markup=sora2pro_aspect_keyboard(aspect))
            return
        if n_frames not in {"10", "15"}:
            await message.answer("⏱️ Выбери длительность ролика: 10 или 15 сек", reply_markup=sora2pro_duration_keyboard(n_frames))
            return

        await _run_sora2_pro_request(
            message=message,
            state=state,
            user=user,
            prompt=prompt,
            image_urls=image_urls or None,
            aspect=aspect,
            n_frames=n_frames,
            sora2_pro_service=sora2_pro_service,
        )

    elif mode == BotModeEnum.passive or not mode:
        await message.answer(
            "👇 Сначала выбери, куда будем делать запрос:",
            reply_markup=mode_keyboard(BotModeEnum.passive),
        )
