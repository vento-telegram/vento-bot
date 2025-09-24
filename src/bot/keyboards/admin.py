from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика по ИИ", callback_data="admin:stats:ai")],
        [InlineKeyboardButton(text="👤 Статистика по пользователю", callback_data="admin:stats:user")],
        [InlineKeyboardButton(text="💵 Настройки цен", callback_data="admin:settings")],
        [InlineKeyboardButton(text="🚫 Блокировка пользователя", callback_data="admin:block")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:start")],
    ])


def admin_ai_stats_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сегодня", callback_data="admin:stats:ai:today")],
        [InlineKeyboardButton(text="Выбрать дату", callback_data="admin:stats:ai:date")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin:home")],
    ])


def admin_settings_keyboard(items: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for key, value in items:
        rows.append([InlineKeyboardButton(text=f"✏️ {key} = {value}", callback_data=f"admin:settings:edit:{key}")])
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="admin:home")]])


