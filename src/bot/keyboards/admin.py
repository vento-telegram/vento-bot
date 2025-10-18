from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_main_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="📊 Выручка за сегодня", callback_data="admin:earnings_today")],
        [InlineKeyboardButton(text="📅 Выручка за дату", callback_data="admin:earnings_by_date")],
        [InlineKeyboardButton(text="➕ Начислить токены", callback_data="admin:add_tokens")],
        [InlineKeyboardButton(text="🚫 Заблокировать пользователя", callback_data="admin:block")],
        [InlineKeyboardButton(text="🔓 Разблокировать пользователя", callback_data="admin:unblock")],
        [InlineKeyboardButton(text="↩️ В начало", callback_data="goto:start")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="↩️ Назад", callback_data="goto:admin")]]
    )

