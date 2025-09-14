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

    rows: list[list[InlineKeyboardButton]] = [
        [
            mode_button("GPT-5", "set_mode:gpt", BotModeEnum.gpt),
            mode_button("GPT-5 Mini", "set_mode:gpt_mini", BotModeEnum.gpt_mini),
        ],
        [
            mode_button("GPT Image", "set_mode:gpt_image", BotModeEnum.gpt_image),
        ],
    ]

    if active_mode == BotModeEnum.gpt_image:
        rows.append([
            InlineKeyboardButton(text="1:1", callback_data="gpt_image:size:1:1"),
            InlineKeyboardButton(text="3:2", callback_data="gpt_image:size:3:2"),
            InlineKeyboardButton(text="2:3", callback_data="gpt_image:size:2:3"),
        ])

    rows.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="goto:start"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)
