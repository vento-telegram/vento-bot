from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.enums import BotModeEnum


def mode_keyboard(active_mode: str | None = None) -> InlineKeyboardMarkup:
    emoji_mapper = {
        BotModeEnum.gpt: "🤖",
        BotModeEnum.gpt_mini: "⚡",
        BotModeEnum.gpt_image: "🖼️",
        BotModeEnum.nano_banana: "🍌",
        BotModeEnum.suno_music: "🎵",
        BotModeEnum.veo_video: "🎬",
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
            mode_button("GPT Image", "set_mode:gpt_image", BotModeEnum.gpt_image),
            mode_button("Nano Banana", "set_mode:nano_banana", BotModeEnum.nano_banana),
        ],
        [
            mode_button("Suno", "set_mode:suno_music", BotModeEnum.suno_music),
            mode_button("Veo Video", "set_mode:veo_video", BotModeEnum.veo_video),
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="goto:start"),
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=rows)


def gpt_image_size_keyboard(selected_size: str) -> InlineKeyboardMarkup:
    sizes = ["1:1", "3:2", "2:3"]
    buttons: list[InlineKeyboardButton] = []
    for s in sizes:
        label = f"✅ {s}" if s == selected_size else s
        buttons.append(InlineKeyboardButton(text=label, callback_data=f"gpt_image:size:{s}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])
