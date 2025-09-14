from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
)
from dependency_injector.wiring import Provide, inject

from bot.constants import settings_models_mapper
from bot.container import Container
from bot.enums import BotModeEnum
from bot.interfaces.services.user import AbcUserService
from bot.interfaces.services.settings import AbcSettingsService
from bot.keyboards.change_ai import mode_keyboard
from bot.keyboards.start import (
    account_keyboard,
    start_keyboard,
)

router = Router()


@router.callback_query(F.data == "set_mode:gpt")
@inject
async def set_mode_chatgpt(
    call: CallbackQuery,
    state: FSMContext,
):
    await state.update_data(mode=BotModeEnum.gpt)
    await call.answer("Режим GPT активирован")
    await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.gpt))
    await call.message.answer(
        "🤖 Теперь на твои сообщения будет отвечать *GPT-5*.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )

@router.callback_query(F.data == "set_mode:gpt_mini")
@inject
async def set_mode_chatgpt_mini(
    call: CallbackQuery,
    state: FSMContext,
):
    await state.update_data(mode=BotModeEnum.gpt_mini)
    await call.answer("Режим GPT Mini активирован")
    await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.gpt_mini))
    await call.message.answer(
        "⚡ Теперь на твои сообщения будет отвечать *GPT-5 Mini*.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )

@router.callback_query(F.data == "goto:account")
@inject
async def goto_account(
    call: CallbackQuery,
    service: AbcUserService = Provide[Container.user_service],
    settings: AbcSettingsService = Provide[Container.settings_service],
):
    await call.answer()

    first_name = call.from_user.first_name
    last_name = call.from_user.last_name if call.from_user.last_name else None
    username = call.from_user.username if call.from_user.username else None
    user = await service.get_user(call.from_user.id)

    display_name_parts = [first_name or ""]
    if last_name:
        display_name_parts.append(f" {last_name}")
    if username:
        display_name_parts.append(f" (@{username})")
    display_name = "".join(display_name_parts)

    daily_bonus = await settings.get_value("daily_bonus")

    await call.message.edit_text(
        text=(
            f"🎟️ *Аккаунт*\n\n"
            f"🐻‍❄️ *{display_name}*\n\n"
            f"🪙 Баланс: *{user.balance}* токенов\n"
            f"🎁 Ежедневно: *{daily_bonus}* токенов\n\n"
            f"👇 Действия:"
        ),
        reply_markup=account_keyboard,
    )


@router.callback_query(F.data == "goto:start")
@inject
async def goto_start(
    call: CallbackQuery,
    state: FSMContext,
    service: AbcUserService = Provide[Container.user_service],
    settings: AbcSettingsService = Provide[Container.settings_service],
):
    await call.answer()

    await state.update_data(history=[])
    user, _ = await service.is_user_new(call.from_user)
    current_mode = (await state.get_data()).get('mode', BotModeEnum.passive)
    text = (
        f"👋 Привет, *{call.from_user.first_name}*!\n\n"
        f"🪙 Твой баланс: *{user.balance}* токенов\n\n"
        f"🤖 Текущий ИИ: *{current_mode}*\n"
    )

    if current_mode != BotModeEnum.passive:
        price = await settings.get_value(settings_models_mapper[current_mode])
        text += f"💸 Цена запроса: *{price} токенов*\n\n"
    else:
        text += "\n"

    text += "👇 Что хочешь сделать?"
    await call.message.edit_text(
        text=text,
        reply_markup=start_keyboard(current_mode, is_admin=bool(user.is_admin)),
    )

@router.callback_query(F.data == "goto:switch")
@inject
async def goto_switch(
    call: CallbackQuery,
    state: FSMContext,
    settings: AbcSettingsService = Provide[Container.settings_service],
):
    current_mode = (await state.get_data()).get("mode", BotModeEnum.passive)

    gpt_price = await settings.get_value(settings_models_mapper[BotModeEnum.gpt])
    mini_price = await settings.get_value(settings_models_mapper[BotModeEnum.gpt_mini])

    text = (
        "👾 *Выбор ИИ*\n\n"
        f"🤖 *GPT‑5* ({gpt_price} токенов/запрос)\n"
        "Самый продвинутый ИИ-чат.\n\n"
        f"⚡ *GPT‑5 Mini* ({mini_price} токенов/запрос)\n"
        "Быстрые и экономные ответы.\n\n"
        "👇 Выбери нужный ИИ:"
    )
    await call.message.edit_text(
        text=text,
        reply_markup=mode_keyboard(current_mode)
    )
    await call.answer("Выбери режим работы")
