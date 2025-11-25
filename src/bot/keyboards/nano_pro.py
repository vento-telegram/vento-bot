from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

NANO_PRO_FORMAT_OPTIONS: tuple[str, ...] = ("16:9", "3:4", "4:3", "1:1", "9:16", "original")
NANO_PRO_FORMAT_LABELS: dict[str, str] = {
    "16:9": "16:9",
    "3:4": "3:4",
    "4:3": "4:3",
    "1:1": "1:1",
    "9:16": "9:16",
    "original": "Исходный",
}


def nano_pro_main_settings_keyboard(selected: str | None) -> InlineKeyboardMarkup:
    label = NANO_PRO_FORMAT_LABELS.get(selected, selected) if selected else "-"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Формат: {label}", callback_data="nano_pro:open:format")],
            [InlineKeyboardButton(text="Назад", callback_data="goto:start")],
        ]
    )


def nano_pro_format_keyboard(selected: str | None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for fmt in NANO_PRO_FORMAT_OPTIONS:
        label = NANO_PRO_FORMAT_LABELS.get(fmt, fmt)
        prefix = "✅ " if fmt == selected else ""
        rows.append([InlineKeyboardButton(text=f"{prefix}{label}", callback_data=f"nano_pro:format:{fmt}")])
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="nano_pro:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

