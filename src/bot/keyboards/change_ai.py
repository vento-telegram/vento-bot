from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.enums import BotModeEnum


def mode_keyboard(active_mode: str = None) -> InlineKeyboardMarkup:
    emoji_mapper = {
        BotModeEnum.gpt5: "🤖",
        BotModeEnum.dalle3: "🎨",
        BotModeEnum.veo: "🎬",
    }

    def mode_button(text, callback, mode_key):
        is_active = mode_key == active_mode
        prefix = "✅ " if is_active else f"{emoji_mapper.get(mode_key, "")} "
        return InlineKeyboardButton(text=f"{prefix}{text}", callback_data=callback)

    return InlineKeyboardMarkup(inline_keyboard=[
        [mode_button("GPT-5", "set_mode:chatgpt", BotModeEnum.gpt5), mode_button("DALL-E 3", "set_mode:dalle", BotModeEnum.dalle3)],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:start")],
    ])
