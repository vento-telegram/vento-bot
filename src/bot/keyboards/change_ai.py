from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.enums import BotModeEnum


def mode_keyboard(active_mode: str | None = None) -> InlineKeyboardMarkup:
    emoji_mapper = {
        BotModeEnum.gpt: "🤖",
        BotModeEnum.gpt_mini: "⚡",
        BotModeEnum.nano_banana: "🏞️",
        BotModeEnum.suno_music: "🎵",
        BotModeEnum.veo_video: "🎬",
        BotModeEnum.sora2_video: "🎥",
    }

    def mode_button(text: str, callback: str, mode_key):
        is_active = mode_key == active_mode
        prefix = "✅ " if is_active else f"{emoji_mapper.get(mode_key, "")} "
        return InlineKeyboardButton(text=f"{prefix}{text}", callback_data=callback)

    rows: list[list[InlineKeyboardButton]] = [
        [
            mode_button("GPT-5", "set_mode:gpt", BotModeEnum.gpt),
            mode_button("GPT-5 Mini", "set_mode:gpt_mini", BotModeEnum.gpt_mini),
        ],
        [
            mode_button("Nano Banana", "set_mode:nano_banana", BotModeEnum.nano_banana),
            mode_button("Suno", "set_mode:suno_music", BotModeEnum.suno_music),
        ],
        [

            mode_button("Veo 3", "set_mode:veo_video", BotModeEnum.veo_video),
            mode_button("Sora 2", "set_mode:sora2_video", BotModeEnum.sora2_video),
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="goto:start"),
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=rows)
