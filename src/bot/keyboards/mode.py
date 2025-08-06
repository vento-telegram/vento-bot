from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.enums import BotModeEnum


def mode_keyboard(active_mode: str = None) -> InlineKeyboardMarkup:
    emoji_mapper = {
        BotModeEnum.chatgpt: "🤖",
        BotModeEnum.dalle: "🎨",
        BotModeEnum.midjourney: "🌌",
        BotModeEnum.veo: "🎬",
    }

    def mode_button(text, callback, mode_key):
        is_active = mode_key == active_mode
        prefix = "✅ " if is_active else f"{emoji_mapper.get(mode_key, "")} "
        return InlineKeyboardButton(text=f"{prefix}{text}", callback_data=callback)

    return InlineKeyboardMarkup(inline_keyboard=[
        [mode_button("ChatGPT", "set_mode:chatgpt", BotModeEnum.chatgpt)],
        [
            mode_button("DALL-E", "set_mode:dalle", BotModeEnum.dalle),
            mode_button("Midjourney (Скоро)", "set_mode:midjourney", BotModeEnum.midjourney),
        ],
        [
            mode_button("Veo-3 (Скоро)", "set_mode:veo", BotModeEnum.veo),
        ]
    ])
