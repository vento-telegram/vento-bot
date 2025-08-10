from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.enums import BotModeEnum


def start_keyboard(current_mode: BotModeEnum, is_admin: bool = False) -> InlineKeyboardMarkup:
    switch_label = "👾 Выбрать ИИ" if current_mode == BotModeEnum.passive else "👾 Сменить ИИ"
    buttons: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="🎟️ Аккаунт", callback_data="goto:account")],
        [InlineKeyboardButton(text=switch_label, callback_data="goto:switch")],
    ]
    if is_admin:
        buttons.insert(0, [InlineKeyboardButton(text="🛠 Админка", callback_data="goto:admin")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

account_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="goto:replenish")],
    [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:start")],
])


replenish_stars_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="200 ⭐", callback_data="buy_star:200")],
    [InlineKeyboardButton(text="500 ⭐", callback_data="buy_star:500")],
    [InlineKeyboardButton(text="1 000 ⭐", callback_data="buy_star:1000")],
    [InlineKeyboardButton(text="2 500 ⭐", callback_data="buy_star:2500")],
    [InlineKeyboardButton(text="5 000 ⭐", callback_data="buy_star:5000")],
    [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:account")],
])