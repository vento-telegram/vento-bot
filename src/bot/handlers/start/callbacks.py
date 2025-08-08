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
async def set_mode_chatgpt(call: CallbackQuery, state: FSMContext):
    await state.update_data(mode=BotModeEnum.gpt5)
    await call.answer("Режим ChatGPT активирован")
    await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.gpt5))
    await call.message.answer(
        "🤖 Теперь на твои сообщения будет отвечать *GPT-5*.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start",
        parse_mode="Markdown",
    )

@router.callback_query(F.data == "set_mode:dalle")
async def set_mode_dalle(call: CallbackQuery, state: FSMContext):
    await state.update_data(mode=BotModeEnum.dalle3)
    await call.answer("Режим DALL-E активирован")
    await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.dalle3))
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
    await call.message.edit_text(
        text=f"🎟️ *Аккаунт*\n\n"
             f"🐻‍❄️ *{first_name}{f" {last_name}" if last_name else ""}{f" (@{username})" if username else ""}*\n\n"
             f"🪙 Баланс: *{user.balance}* токенов\n"
             f"🎁 Ежедневно: *+200* токенов\n\n"
             f"👇 Действия:",
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
            f"🪙 Твой баланс: *{user.balance:g} токенов*\n\n"
            f"🤖 Текущий ИИ: *{mode}*\n"
            f"💸 Цена запроса: *{price} токенов*\n\n"
            f"👇 Что хочешь сделать?"
        ),
        reply_markup=start_keyboard(mode),
        parse_mode=ParseMode.MARKDOWN,
    )

@router.callback_query(F.data == "goto:switch")
async def goto_switch(call: CallbackQuery):
    await call.message.edit_text(
        text="👇 Выбери нужный ИИ:",
        reply_markup=mode_keyboard(BotModeEnum.passive),
        parse_mode=ParseMode.MARKDOWN,
    )
    await call.answer("Выбери режим работы")
