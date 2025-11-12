from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

NANO_FORMAT_OPTIONS: tuple[str, ...] = ("16:9", "4:3", "1:1", "9:16")


def nano_main_settings_keyboard(selected: str | None) -> InlineKeyboardMarkup:
    label = selected if selected else "-"
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
        text = f"✓ {option}" if option == selected else option
        current_row.append(InlineKeyboardButton(text=text, callback_data=f"nano:format:{option}"))
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="nano:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

