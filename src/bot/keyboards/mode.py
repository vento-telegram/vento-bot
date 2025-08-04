from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

mode_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="🤖 ChatGPT", callback_data="set_mode:chatgpt"),
        InlineKeyboardButton(text="🎞️ Veo-3", callback_data="set_mode:veo3"),
    ]
])
