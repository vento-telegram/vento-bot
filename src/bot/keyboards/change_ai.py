from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.enums import BotModeEnum


def mode_keyboard(active_mode: str | None = None, gpt5_available: bool = True) -> InlineKeyboardMarkup:
    emoji_mapper = {
        BotModeEnum.gpt5: "🤖",
        BotModeEnum.gpt5_mini: "🤖",
        BotModeEnum.dalle3: "🎨",
        BotModeEnum.veo: "🎬",
    }

    def mode_button(text: str, callback: str, mode_key):
        is_active = mode_key == active_mode
        prefix = "✅ " if is_active else f"{emoji_mapper.get(mode_key, "")} "
        return InlineKeyboardButton(text=f"{prefix}{text}", callback_data=callback)

    gpt_button = (
        mode_button("GPT-5", "set_mode:chatgpt", BotModeEnum.gpt5)
        if gpt5_available
        else mode_button("GPT-5 Mini", "set_mode:chatgpt_mini", BotModeEnum.gpt5_mini)
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [gpt_button, mode_button("DALL-E 3", "set_mode:dalle", BotModeEnum.dalle3)],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:start")],
        ]
    )
