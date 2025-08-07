from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


start_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎟️ Аккаунт", callback_data="goto:account")],
    [InlineKeyboardButton(text="👾 Сменить ИИ", callback_data="goto:switch")],
])

account_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="goto:replenish")],
    [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:start")],
])
