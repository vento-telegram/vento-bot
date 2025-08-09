from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from dependency_injector.wiring import Provide, inject

from bot.container import Container
from bot.enums import BotModeEnum
from bot.interfaces.services.user import AbcUserService
from bot.interfaces.services.pricing import AbcPricingService
from bot.keyboards.change_ai import mode_keyboard
from bot.keyboards.start import account_keyboard, start_keyboard

router = Router()


@router.callback_query(F.data == "set_mode:chatgpt")
@inject
async def set_mode_chatgpt(
    call: CallbackQuery,
    state: FSMContext,
    pricing: AbcPricingService = Provide[Container.pricing_service],
    service: AbcUserService = Provide[Container.user_service],
):
    user = await service.get_user(call.from_user.id)
    can_afford = await pricing.ensure_user_can_afford(user.balance, BotModeEnum.gpt5)
    if not can_afford:
        # Switch to GPT-5 Mini immediately with a clear notification
        await state.update_data(mode=BotModeEnum.gpt5_mini)
        await call.answer("Недостаточно токенов для GPT-5. Переключаю на GPT-5 Mini.", show_alert=True)
        await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.gpt5_mini, gpt5_available=False))
        await call.message.answer(
            "ℹ️ Недостаточно токенов для GPT‑5 — активирован *GPT‑5 Mini*.",
            parse_mode="Markdown",
        )
        return
    await state.update_data(mode=BotModeEnum.gpt5)
    await call.answer("Режим ChatGPT активирован")
    await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.gpt5, gpt5_available=True))
    await call.message.answer(
        "🤖 Теперь на твои сообщения будет отвечать *GPT-5*.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start",
        parse_mode="Markdown",
    )

@router.callback_query(F.data == "set_mode:chatgpt_mini")
@inject
async def set_mode_chatgpt_mini(
    call: CallbackQuery,
    state: FSMContext,
    pricing: AbcPricingService = Provide[Container.pricing_service],
    service: AbcUserService = Provide[Container.user_service],
):
    user = await service.get_user(call.from_user.id)
    can_afford_mini = await pricing.ensure_user_can_afford(user.balance, BotModeEnum.gpt5_mini)
    if not can_afford_mini:
        await call.answer("Недостаточно токенов для GPT-5 Mini.", show_alert=True)
        return
    await state.update_data(mode=BotModeEnum.gpt5_mini)
    await call.answer("Режим GPT-5 Mini активирован")
    await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.gpt5_mini, gpt5_available=False))
    await call.message.answer(
        "🤖 Теперь на твои сообщения будет отвечать *GPT-5 Mini*.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start",
        parse_mode="Markdown",
    )

@router.callback_query(F.data == "set_mode:dalle")
@inject
async def set_mode_dalle(
    call: CallbackQuery,
    state: FSMContext,
    pricing: AbcPricingService = Provide[Container.pricing_service],
    service: AbcUserService = Provide[Container.user_service],
):
    user = await service.get_user(call.from_user.id)
    can_afford = await pricing.ensure_user_can_afford(user.balance, BotModeEnum.dalle3)
    if not can_afford:
        await call.answer("Недостаточно токенов для DALL·E 3.", show_alert=True)
        return
    await state.update_data(mode=BotModeEnum.dalle3)
    await call.answer("Режим DALL-E активирован")
    can_gpt5 = await pricing.ensure_user_can_afford(user.balance, BotModeEnum.gpt5)
    await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.dalle3, gpt5_available=can_gpt5))
    await call.message.answer(
        "🖼️ Теперь в ответ на твои сообщения *DALL-E 3* будет генерировать изображения.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start",
        parse_mode="Markdown",
    )

@router.callback_query(F.data == "goto:account")
@inject
async def goto_account(
    call: CallbackQuery,
    service: AbcUserService = Provide[Container.user_service],
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

    await call.message.edit_text(
        text=(
            f"🎟️ *Аккаунт*\n\n"
            f"🐻‍❄️ *{display_name}*\n\n"
            f"🪙 Баланс: *{user.balance}* токенов\n"
            f"🎁 Ежедневно: *+150* токенов\n\n"
            f"👇 Действия:"
        ),
        reply_markup=account_keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )



@router.callback_query(F.data == "goto:start")
@inject
async def goto_start(
    call: CallbackQuery,
    state: FSMContext,
    service: AbcUserService = Provide[Container.user_service],
    pricing: AbcPricingService = Provide[Container.pricing_service],
):
    await call.answer()

    await state.update_data(history=[])
    user, _ = await service.is_user_new(call.from_user)
    mode = (await state.get_data()).get('mode', BotModeEnum.passive)
    price = await pricing.get_price_for_mode(mode)
    await call.message.edit_text(
        text=(
            f"👋 Привет, *{call.from_user.first_name}*!\n\n"
            f"🪙 Твой баланс: *{user.balance} токенов*\n\n"
            f"🤖 Текущий ИИ: *{mode}*\n"
            f"💸 Цена запроса: *{price} токенов*\n\n"
            f"👇 Что хочешь сделать?"
        ),
        reply_markup=start_keyboard(mode, is_admin=bool(user.is_admin)),
        parse_mode=ParseMode.MARKDOWN,
    )

@router.callback_query(F.data == "goto:switch")
@inject
async def goto_switch(
    call: CallbackQuery,
    state: FSMContext,
    service: AbcUserService = Provide[Container.user_service],
    pricing: AbcPricingService = Provide[Container.pricing_service],
):
    user = await service.get_user(call.from_user.id)
    can_gpt5 = await pricing.ensure_user_can_afford(user.balance, BotModeEnum.gpt5)
    current_mode = (await state.get_data()).get("mode", BotModeEnum.passive)

    text = (
        "👾 *Выбор ИИ*\n\n"
        "🤖 *GPT‑5* (10 токенов/запрос)\n"
        "Самый продвинутый ИИ-чат.\n\n"
        "⚡ *GPT‑5 Mini* (Бесплатно)\n"
        "Включается по истечению токенов.\n\n"
        "🎨 *DALL·E 3* (40 токенов/запрос)\n"
        "Лучший генератор изображений.\n\n"
        "👇 Выбери нужный ИИ:"
    )
    await call.message.edit_text(
        text=text,
        reply_markup=mode_keyboard(current_mode, gpt5_available=can_gpt5),
        parse_mode=ParseMode.MARKDOWN,
    )
    await call.answer("Выбери режим работы")
