from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def veo_aspect_keyboard(selected: str | None = None) -> InlineKeyboardMarkup:
    options = ["16:9", "9:16"]
    buttons: list[InlineKeyboardButton] = []
    for opt in options:
        label = f"✅ {opt}" if opt == selected else opt
        buttons.append(InlineKeyboardButton(text=label, callback_data=f"veo:aspect:{opt}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons, [InlineKeyboardButton(text="🔙 Назад", callback_data="veo:back")]])


def veo_quality_keyboard(standard_price: int, improved_price: int, selected: str | None = None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    std_label = "✅ Стандарт — {p}".format(p=standard_price) if selected == 'standard' else "Стандарт — {p}".format(p=standard_price)
    imp_label = "✅ Улучшенное — {p}".format(p=improved_price) if selected == 'improved' else "Улучшенное — {p}".format(p=improved_price)
    rows.append([
        InlineKeyboardButton(text=std_label + " ток.", callback_data="veo:quality:standard"),
        InlineKeyboardButton(text=imp_label + " ток.", callback_data="veo:quality:improved"),
    ])
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="veo:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def veo_settings_keyboard(aspect: str, quality: str, standard_price: int, improved_price: int) -> InlineKeyboardMarkup:
    # Single menu: first row quality (with prices), second row aspect options, third row back
    std_selected = quality == 'standard'
    imp_selected = quality == 'improved'
    std_label = ("✅ Стандарт — {p} ток.".format(p=standard_price)) if std_selected else ("Стандарт — {p} ток.".format(p=standard_price))
    imp_label = ("✅ Улучшенное — {p} ток.".format(p=improved_price)) if imp_selected else ("Улучшенное — {p} ток.".format(p=improved_price))

    q_row = [
        InlineKeyboardButton(text=std_label, callback_data="veo:quality:standard"),
        InlineKeyboardButton(text=imp_label, callback_data="veo:quality:improved"),
    ]

    a_row: list[InlineKeyboardButton] = []
    for opt in ["16:9", "9:16"]:
        label = f"✅ {opt}" if opt == aspect else opt
        a_row.append(InlineKeyboardButton(text=label, callback_data=f"veo:aspect:{opt}"))

    back_row = [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:start")]

    return InlineKeyboardMarkup(inline_keyboard=[q_row, a_row, back_row])


def veo_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="goto:start")]])


