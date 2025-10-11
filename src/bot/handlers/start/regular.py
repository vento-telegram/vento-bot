import logging

from aiogram import Router, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dependency_injector.wiring import Provide, inject
from urllib.parse import parse_qs

from bot.constants import settings_models_mapper
from bot.container import Container
from bot.enums import BotModeEnum
from bot.interfaces.services.settings import AbcSettingsService
from bot.interfaces.services.user import AbcUserService
from bot.keyboards.start import start_keyboard

logger = logging.getLogger(__name__)

router = Router()

@router.message(CommandStart())
@inject
async def start_handler(
    message: Message,
    state: FSMContext,
    admin_bot: Bot = Provide[Container.admin_bot],
    user_service: AbcUserService = Provide[Container.user_service],
    settings_service: AbcSettingsService = Provide[Container.settings_service],
):
    state_data = await state.get_data()
    ref_from: str | None = None
    try:
        raw_text = (message.text or "").strip()
        parts = raw_text.split(maxsplit=1)
        if len(parts) > 1:
            payload = parts[1].lstrip('?')
            if payload.lower().startswith('start='):
                ref_from = payload.split('=', 1)[1] or None
            else:
                params = parse_qs(payload, keep_blank_values=True)
                if 'start' in params and params['start']:
                    ref_from = params['start'][0] or None
                else:
                    # Treat bare token as the ref value
                    ref_from = payload or None
    except Exception:
        ref_from = None

    user, is_new = await user_service.is_user_new(message.from_user, ref_from=ref_from)
    if is_new:
        await state.update_data(history=[], mode=BotModeEnum.passive)
        start_bonus = await settings_service.get_value("start_bonus")
        await message.answer(
            text=(
                "🎉 Добро пожаловать, я *Vento*!\n\n"
                "*Что я умею:*\n"
                "🧠 Отвечаю на самые сложные вопросы с помощью *GPT-5*\n"
                "⚡ Быстрые и экономные ответы в режиме *GPT-5 Mini*\n"
                "🖼️ Генерирую и редактирую изображения с *GPT Image* и *Nano Banana*\n"
                "🎵 Создаю музыкальные шедевры с помощью *Suno*\n"
                "🎬 Генерирую видео с *Veo 3* и *Sora 2* по описанию и оживляю фото\n\n"
                f"🎁 Тебе уже начислено *{start_bonus}* стартовых токенов — можно сразу начать!\n"
                f"🗓️ Каждый день твой баланс будет *бесплатно* пополнятся до *50 токенов*!\n"
                "Для возвращения в меню всегда поможет команда /start."
            )
        )
        try:
            admins = await user_service.list_admins()
            logger.info(f"Notify ADMINS: {admins}")
            admin_text = (
                "🆕 *Новый пользователь:*\n\n"
                f"ID: {message.from_user.id} (@{message.from_user.username})\nРеферал: {ref_from if ref_from else '-'}"
            )
            for admin in admins:
                try:
                    await admin_bot.send_message(admin.telegram_id, admin_text)
                except Exception as e:
                    logger.info(f"Exception while sending message to {admin.telegram_id}. {e}")
                    pass
        except Exception as e:
            logger.info(f"Exception while sending message. {e}")
            pass

    current_mode = state_data.get('mode', BotModeEnum.passive)
    daily_bonus = await settings_service.get_value("daily_bonus")

    text = (
        f"👋 Привет, *{message.from_user.first_name}*!\n\n"
        f"🪙 Твой баланс: *{user.balance}* токенов\n"
    )
    try:
        user_balance_int = int(user.balance)
    except Exception:
        user_balance_int = 0
    if user_balance_int <= 50:
        text += f"⚡ Ежедневно: до *{daily_bonus}* токенов\n\n"
    else:
        text += "\n"
    text += f"🤖 Текущий ИИ: *{current_mode}*\n"

    if current_mode != BotModeEnum.passive:
        price = await settings_service.get_value(settings_models_mapper[current_mode])
        text += f"💸 Цена запроса: *{price} токенов*\n\n"
    else:
        text += "\n"

    text += "👇 Что хочешь сделать?"

    kb = start_keyboard(current_mode)

    await message.answer(
        text=text,
        reply_markup=kb,
    )
