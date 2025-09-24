from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_main_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="➕ Начислить токены", callback_data="admin:add_tokens")],
        [InlineKeyboardButton(text="🚫 Заблокировать пользователя", callback_data="admin:block")],
        [InlineKeyboardButton(text="✅ Разблокировать пользователя", callback_data="admin:unblock")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:start")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="goto:admin")]]
    )

