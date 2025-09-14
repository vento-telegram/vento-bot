from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.enums import BotModeEnum


def mode_keyboard(active_mode: str | None = None) -> InlineKeyboardMarkup:
    emoji_mapper = {
        BotModeEnum.gpt: "🤖",
        BotModeEnum.gpt_mini: "⚡",
        BotModeEnum.gpt_image: "🖼️",
    }

    def mode_button(text: str, callback: str, mode_key):
        is_active = mode_key == active_mode
        prefix = "✅ " if is_active else f"{emoji_mapper.get(mode_key, "")} "
        return InlineKeyboardButton(text=f"{prefix}{text}", callback_data=callback)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                mode_button("GPT-5", "set_mode:gpt", BotModeEnum.gpt),
                mode_button("GPT-5 Mini", "set_mode:gpt_mini", BotModeEnum.gpt_mini),
            ],
            [
                mode_button("GPT Image", "set_mode:gpt_image", BotModeEnum.gpt_image),
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="goto:start"),
            ],
        ]
    )
