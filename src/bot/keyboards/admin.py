from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_main_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="📊 Запросы по моделям (сегодня)", callback_data="admin:stats:today")],
        [InlineKeyboardButton(text="📅 Запросы по моделям на дату", callback_data="admin:stats:bydate")],
        [InlineKeyboardButton(text="👤 Статистика пользователя", callback_data="admin:userstats")],
        [InlineKeyboardButton(text="⚙️ Настройки (показать)", callback_data="admin:settings:list")],
        [InlineKeyboardButton(text="✏️ Изменить настройку", callback_data="admin:settings:set")],
        [InlineKeyboardButton(text="⛔ Заблокировать пользователя", callback_data="admin:block")],
        [InlineKeyboardButton(text="✅ Разблокировать пользователя", callback_data="admin:unblock")],
        [InlineKeyboardButton(text="🔙 Выйти", callback_data="goto:start")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="admin:menu")]])


