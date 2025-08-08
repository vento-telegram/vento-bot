from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.enums import BotModeEnum


def start_keyboard(current_mode: BotModeEnum) -> InlineKeyboardMarkup:
    switch_label = "👾 Выбрать ИИ" if current_mode == BotModeEnum.passive else "👾 Сменить ИИ"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎟️ Аккаунт", callback_data="goto:account")],
        [InlineKeyboardButton(text=switch_label, callback_data="goto:switch")],
    ])

account_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="goto:replenish")],
    [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:start")],
])
