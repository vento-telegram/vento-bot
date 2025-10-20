from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def sora2pro_aspect_keyboard(selected: str | None = None) -> InlineKeyboardMarkup:
    options = ["16:9", "9:16"]
    buttons: list[InlineKeyboardButton] = []
    for opt in options:
        label = f"✅ {opt}" if opt == selected else opt
        buttons.append(InlineKeyboardButton(text=label, callback_data=f"sora2pro:aspect:{opt}"))
    return InlineKeyboardMarkup(
        inline_keyboard=[
            buttons,
            [InlineKeyboardButton(text="🔙 Назад", callback_data="sora2pro:main")],
        ]
    )


def sora2pro_duration_keyboard(selected: str | None = None) -> InlineKeyboardMarkup:
    options = ["10", "15"]
    buttons: list[InlineKeyboardButton] = []
    for opt in options:
        label = f"✅ {opt} секунд" if opt == selected else f"{opt} секунд"
        buttons.append(InlineKeyboardButton(text=label, callback_data=f"sora2pro:frames:{opt}"))
    return InlineKeyboardMarkup(
        inline_keyboard=[
            buttons,
            [InlineKeyboardButton(text="🔙 Назад", callback_data="sora2pro:main")],
        ]
    )


def sora2pro_main_settings_keyboard(aspect: str | None, n_frames: str | None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    aspect_text = aspect or "—"
    duration_text = (f"{n_frames} секукнд" if n_frames in {"10", "15"} else "—")
    rows.append([InlineKeyboardButton(text=f"Формат: {aspect_text}", callback_data="sora2pro:open:aspect")])
    rows.append([InlineKeyboardButton(text=f"Длительность: {duration_text}", callback_data="sora2pro:open:frames")])
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="goto:start")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

