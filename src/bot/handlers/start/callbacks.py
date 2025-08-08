from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from dependency_injector.wiring import Provide, inject

from bot.container import Container
from bot.enums import BotModeEnum
from bot.interfaces.services.user import AbcUserService
from bot.keyboards.change_ai import mode_keyboard
from bot.keyboards.start import account_keyboard, start_keyboard

router = Router()


@router.callback_query(F.data == "set_mode:chatgpt")
async def set_mode_chatgpt(call: CallbackQuery, state: FSMContext):
    await state.update_data(mode=BotModeEnum.gpt5)
    await call.answer("Режим ChatGPT активирован")
    await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.gpt5))
    await call.message.answer(
        "🤖 Теперь на твои сообщения будет отвечать *ChatGPT*.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start",
        parse_mode="Markdown",
    )

@router.callback_query(F.data == "set_mode:dalle")
async def set_mode_dalle(call: CallbackQuery, state: FSMContext):
    await state.update_data(mode=BotModeEnum.dalle3)
    await call.answer("Режим DALL-E активирован")
    await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.dalle3))
    await call.message.answer(
        "🖼️ Теперь в ответ на твои сообщения *DALL-E* будет генерировать изображения.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start",
        parse_mode="Markdown",
    )

@router.callback_query(F.data == "goto:account")
async def goto_account(call: CallbackQuery):
    first_name = call.from_user.first_name
    last_name = call.from_user.last_name if call.from_user.last_name else None
    username = call.from_user.username if call.from_user.username else None
    await call.message.edit_text(
        text=f"🎟️ *Аккаунт*\n\n"
             f"*{first_name}{f" {last_name}" if last_name else ""}{f" (@{username})" if username else ""}*\n\n"
             f"🪙 Баланс: *200* токенов\n\n"
             f"🎁 Ежедневное пополнение: *200* токенов\n"
             f"📊 Лимит бесплатного пополнения: *300* токенов\n\n"
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
):
    await state.update_data(history=[])
    is_new = await service.is_user_new(call.from_user)
    if is_new:
        pass
    await call.message.edit_text(
        text=f"👋 Привет, *{call.from_user.first_name}*!\n\n"
             f"🪙 Твой баланс: *200 токенов*\n\n"
             f"🤖 Текущий ИИ: *GPT-4.5*\n"
             f"💸 Цена за запрос: *5 токенов*\n\n"
             f"👇 Что хочешь сделать?",
        reply_markup=start_keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )

@router.callback_query(F.data == "goto:switch")
async def goto_switch(call: CallbackQuery):
    await call.message.edit_text(
        text="👇 Выбери режим, в котором будем работать:",
        reply_markup=mode_keyboard(BotModeEnum.passive),
        parse_mode=ParseMode.MARKDOWN,
    )
    await call.answer("Выбери режим работы")
