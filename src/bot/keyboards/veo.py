from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def veo_aspect_keyboard(selected: str | None = None) -> InlineKeyboardMarkup:
    options = ["16:9", "9:16"]
    buttons: list[InlineKeyboardButton] = []
    for opt in options:
        label = f"✅ {opt}" if opt == selected else opt
        buttons.append(InlineKeyboardButton(text=label, callback_data=f"veo:aspect:{opt}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons, [InlineKeyboardButton(text="🔙 Назад", callback_data="veo:main")]])


def veo_quality_keyboard(standard_price: int, improved_price: int, selected: str | None = None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    std_label = "✅ Стандарт" if selected == 'standard' else "Стандарт"
    imp_label = "✅ Улучшенное" if selected == 'improved' else "Улучшенное"
    rows.append([
        InlineKeyboardButton(text=std_label, callback_data="veo:quality:standard"),
        InlineKeyboardButton(text=imp_label, callback_data="veo:quality:improved"),
    ])
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="veo:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)



def veo_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="goto:start")]])


def veo_main_settings_keyboard(aspect: str | None, quality: str | None, standard_price: int, improved_price: int) -> InlineKeyboardMarkup:
    if quality == 'standard':
        quality_text = "Стандарт"
    elif quality == 'improved':
        quality_text = "Улучшенное"
    else:
        quality_text = "—"
    aspect_text = aspect if aspect else "—"
    rows: list[list[InlineKeyboardButton]] = []
    rows.append([InlineKeyboardButton(text=f"Качество: {quality_text}", callback_data="veo:open:quality")])
    rows.append([InlineKeyboardButton(text=f"Формат: {aspect_text}", callback_data="veo:open:aspect")])
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="goto:start")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


