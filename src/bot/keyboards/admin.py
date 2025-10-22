from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_main_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="ðŸ“Š Ð’Ñ‹Ñ€ÑƒÑ‡ÐºÐ° Ð·Ð° ÑÐµÐ³Ð¾Ð´Ð½Ñ", callback_data="admin:earnings_today"),
            InlineKeyboardButton(text="ðŸ“… Ð’Ñ‹Ñ€ÑƒÑ‡ÐºÐ° Ð·Ð° Ð´Ð°Ñ‚Ñƒ", callback_data="admin:earnings_by_date"),
        ],
        [
            InlineKeyboardButton(text="ðŸ‘¥ ÐŸÐ¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ñ‚ÐµÐ»ÐµÐ¹ Ð·Ð° ÑÐµÐ³Ð¾Ð´Ð½Ñ", callback_data="admin:users_today"),
        ],
        [
            InlineKeyboardButton(text="Актив за сегодня", callback_data="admin:active_today"),
        ],
        [
            InlineKeyboardButton(text="ðŸ‘¥ ÐŸÐ¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ñ‚ÐµÐ»ÐµÐ¹ Ð·Ð° Ð´Ð°Ñ‚Ñƒ", callback_data="admin:users_by_date"),
        ],
        [
            InlineKeyboardButton(text="ðŸ‘¥ Ð’ÑÐµÐ³Ð¾ Ð¿Ð¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ñ‚ÐµÐ»ÐµÐ¹", callback_data="admin:users_total"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="â†©ï¸ ÐÐ°Ð·Ð°Ð´", callback_data="goto:admin")]]
    )

