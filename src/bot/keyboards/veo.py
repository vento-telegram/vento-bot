from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def veo_prompt_keyboard(selected_ar: str = "16:9") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Соотношение сторон: {selected_ar}", callback_data="veo:show_ar_options")],
            [
                InlineKeyboardButton(text="📋 Примеры", callback_data="ignore"),
                InlineKeyboardButton(text="ℹ️ Инструкция", url="https://teletype.in/@visvist/8NrWcbP43mH"),
            ],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="goto:switch")],
        ]
    )


def veo_ar_options_keyboard(selected_ar: str) -> InlineKeyboardMarkup:
    def mark(ar: str) -> str:
        return f"✅ {ar}" if ar == selected_ar else ar

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=mark("16:9"), callback_data="veo:set_ar:16:9"),
                InlineKeyboardButton(text=mark("9:16"), callback_data="veo:set_ar:9:16"),
                InlineKeyboardButton(text=mark("1:1"), callback_data="veo:set_ar:1:1"),
            ],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="veo:show_prompt")],
        ]
    )


