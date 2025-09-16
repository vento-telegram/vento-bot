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
from aiogram.exceptions import TelegramBadRequest

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
                # Try to send the first part with markdown parsing
                try:
                    await status_msg.edit_text(parts[0])
                except TelegramBadRequest as e:
                    logger.exception("edit_text markdown error on part=0 len=%d: %s", len(parts[0]), str(e))
                    # Fallback 1: Try without markdown parsing
                    try:
                        await status_msg.edit_text(parts[0], parse_mode=None)
                    except Exception as fallback_e:
                        logger.exception("edit_text fallback failed: %s", str(fallback_e))
                        # Fallback 2: Try with HTML parsing as last resort
                        try:
                            await status_msg.edit_text(parts[0], parse_mode="HTML")
                        except Exception:
                            logger.exception("edit_text HTML fallback also failed")
                            # Final fallback: Send as plain text with truncation if needed
                            try:
                                safe_text = parts[0][:4000] + "..." if len(parts[0]) > 4000 else parts[0]
                                await status_msg.edit_text(safe_text, parse_mode=None)
                            except Exception:
                                logger.exception("All fallbacks failed for first part")
                
                # Send additional parts
                for idx, extra in enumerate(parts[1:], start=1):
                    try:
                        await message.answer(extra)
                    except TelegramBadRequest as e:
                        logger.exception("answer markdown error on part=%d len=%d: %s", idx, len(extra), str(e))
                        try:
                            await message.answer(extra, parse_mode=None)
                        except Exception as fallback_e:
                            logger.exception("answer fallback failed for part=%d: %s", idx, str(fallback_e))
                            # Try HTML parsing as last resort
                            try:
                                await message.answer(extra, parse_mode="HTML")
                            except Exception:
                                logger.exception("answer HTML fallback also failed for part=%d", idx)
                                # Final fallback: Send truncated plain text
                                try:
                                    safe_text = extra[:4000] + "..." if len(extra) > 4000 else extra
                                    await message.answer(safe_text, parse_mode=None)
                                except Exception:
                                    logger.exception("All fallbacks failed for part=%d", idx)
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
