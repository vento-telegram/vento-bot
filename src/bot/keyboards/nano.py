from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

NANO_FORMAT_OPTIONS: tuple[str, ...] = ("16:9", "3:4", "4:3", "1:1", "9:16", "original")
NANO_FORMAT_LABELS: dict[str, str] = {
    "16:9": "16:9",
    "3:4": "3:4",
    "4:3": "4:3",
    "1:1": "1:1",
    "9:16": "9:16",
    "original": "Исходный",
}


def nano_main_settings_keyboard(selected: str | None) -> InlineKeyboardMarkup:
    label = NANO_FORMAT_LABELS.get(selected, selected) if selected else "-"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Формат: {label}", callback_data="nano:open:format")],
            [InlineKeyboardButton(text="Назад", callback_data="goto:start")],
        ]
    )


def nano_format_keyboard(selected: str | None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    current_row: list[InlineKeyboardButton] = []
    for option in NANO_FORMAT_OPTIONS:
        label = NANO_FORMAT_LABELS.get(option, option)
        text = f"✓ {label}" if option == selected else label
        current_row.append(InlineKeyboardButton(text=text, callback_data=f"nano:format:{option}"))
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="nano:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
