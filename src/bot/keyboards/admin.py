from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_main_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="📊 Выручка за сегодня", callback_data="admin:earnings_today"),
            InlineKeyboardButton(text="📅 Выручка за дату", callback_data="admin:earnings_by_date"),
        ],
        [
            InlineKeyboardButton(text="👥 Пользователей за сегодня", callback_data="admin:users_today"),
        ],
        [
            InlineKeyboardButton(text="Актив за сегодня", callback_data="admin:active_today"),
        ],
        [
            InlineKeyboardButton(text="👥 Пользователей за дату", callback_data="admin:users_by_date"),
        ],
        [
            InlineKeyboardButton(text="👥 Всего пользователей", callback_data="admin:users_total"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="↩️ Назад", callback_data="goto:admin")]]
    )

