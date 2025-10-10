from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def sora2_aspect_keyboard(selected: str | None = None) -> InlineKeyboardMarkup:
    options = ["16:9", "9:16"]
    buttons: list[InlineKeyboardButton] = []
    for opt in options:
        label = f"✔ {opt}" if opt == selected else opt
        buttons.append(InlineKeyboardButton(text=label, callback_data=f"sora2:aspect:{opt}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons, [InlineKeyboardButton(text="🔙 Назад", callback_data="sora2:main")]])


def sora2_main_settings_keyboard(aspect: str | None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    aspect_text = aspect or "не выбран"
    rows.append([InlineKeyboardButton(text=f"Формат: {aspect_text}", callback_data="sora2:open:aspect")])
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="goto:start")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

