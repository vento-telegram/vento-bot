from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


SUNO_STYLE_PRESETS: list[tuple[str, str]] = [
    ("pop", "Pop"),
    ("rock", "Rock"),
    ("hiphop", "Hip‑hop"),
    ("edm", "EDM"),
    ("electronic", "Electronic"),
    ("lofi", "Lo‑fi"),
    ("jazz", "Jazz"),
    ("classical", "Classical"),
    ("ambient", "Ambient"),
    ("folk", "Folk"),
]


def suno_styles_keyboard(selected_slug: str | None = None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    # 2 columns
    for i in range(0, len(SUNO_STYLE_PRESETS), 2):
        chunk = SUNO_STYLE_PRESETS[i:i+2]
        row: list[InlineKeyboardButton] = []
        for slug, label in chunk:
            text = f"✅ {label}" if slug == selected_slug else label
            row.append(InlineKeyboardButton(text=text, callback_data=f"suno:style:{slug}"))
        rows.append(row)

    rows.append([InlineKeyboardButton(text="🎛 Свой стиль", callback_data="suno:style:custom")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def suno_prompt_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="suno:change_style")],
    ])


def suno_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="suno:change_style")],
    ])


def suno_vocals_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_data="suno:vocals:yes"), InlineKeyboardButton(text="Нет", callback_data="suno:vocals:no")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="suno:change_style")],
    ])


def suno_input_mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Свой текст", callback_data="suno:im:custom")],
        [InlineKeyboardButton(text="🖊 Описание", callback_data="suno:im:desc")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="suno:vocals:back")],
    ])


