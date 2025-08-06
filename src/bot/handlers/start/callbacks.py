from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.enums import BotModeEnum
from bot.keyboards.mode import mode_keyboard


router = Router()


@router.callback_query(F.data == "set_mode:chatgpt")
async def set_mode_chatgpt(call: CallbackQuery, state: FSMContext):
    await state.update_data(mode=BotModeEnum.chatgpt)
    await call.answer("Режим ChatGPT активирован")
    await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.chatgpt))
    await call.message.answer(
        "🤖 Теперь на твои сообщения будет отвечать *ChatGPT*.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start",
        parse_mode="Markdown",
    )

@router.callback_query(F.data == "set_mode:dalle")
async def set_mode_dalle(call: CallbackQuery, state: FSMContext):
    await state.update_data(mode=BotModeEnum.dalle)
    await call.answer("Режим DALL-E активирован")
    await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.dalle))
    await call.message.answer(
        "🖼️ Теперь в ответ на твои сообщения *DALL-E* будет генерировать изображения.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start",
        parse_mode="Markdown",
    )
