import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from dependency_injector.wiring import Provide, inject

from bot.container import Container
from bot.enums import BotModeEnum
from bot.errors import InsufficientBalanceError
from bot.interfaces.services.sora2 import AbcSora2Service
from bot.interfaces.services.user import AbcUserService

logger = logging.getLogger(__name__)

router = Router()


async def _get_telegram_file_url(bot, file_id: str) -> str:
    file = await bot.get_file(file_id)
    return f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"


@router.message()
@inject
async def sora2_message_handler(
    message: Message,
    state: FSMContext,
    sora2_service: AbcSora2Service = Provide[Container.sora2_service],
    user_service: AbcUserService = Provide[Container.user_service],
):
    state_data = await state.get_data()
    mode = state_data.get("mode")
    if mode != BotModeEnum.sora2_video:
        return

    user = await user_service.get_user(message.from_user.id)
    if user.is_blocked:
        return

    aspect = state_data.get("sora_aspect")

    image_urls: list[str] = []
    prompt: str = ""
    if message.photo:
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
    elif message.document and (message.document.mime_type or "").lower().startswith("image/"):
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
            await message.answer("Пришли текст или картинку с описанием")
            return
        prompt = text

    if not aspect:
        await message.answer("Сначала выбери формат: 16:9 или 9:16")
        return

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
                "*☹️ Недостаточно токенов*\n\nПополни баланс или выбери другую модель.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="goto:replenish"), InlineKeyboardButton(text="🔀 Сменить режим", callback_data="goto:switch")]],
                ),
            )
        except Exception:
            await message.answer(
                "*☹️ Недостаточно токенов*\n\nПополни баланс или выбери другую модель.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="goto:replenish"), InlineKeyboardButton(text="🔀 Сменить режим", callback_data="goto:switch")]],
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

