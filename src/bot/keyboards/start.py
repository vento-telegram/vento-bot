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


replenish_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="1 000 🪙 — 100 ₽", callback_data="buy:1000")],
    [InlineKeyboardButton(text="5 000 🪙 — 500 ₽", callback_data="buy:5000")],
    [InlineKeyboardButton(text="10 500 🪙 — 1 000 ₽", callback_data="buy:10500")],
    [InlineKeyboardButton(text="21 600 🪙 — 2 000 ₽", callback_data="buy:21600")],
    [InlineKeyboardButton(text="55 500 🪙 — 5 000 ₽", callback_data="buy:55500")],
    [InlineKeyboardButton(text="⭐ Оплатить звёздами", callback_data="goto:replenish_stars")],
    [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:account")],
])


replenish_stars_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="1 000 🪙 — 170 ⭐", callback_data="buy_star:1000")],
    [InlineKeyboardButton(text="5 000 🪙 — 810 ⭐", callback_data="buy_star:5000")],
    [InlineKeyboardButton(text="10 500 🪙 — 1 650 ⭐", callback_data="buy_star:10500")],
    [InlineKeyboardButton(text="21 600 🪙 — 3 300 ⭐", callback_data="buy_star:21600")],
    [InlineKeyboardButton(text="55 500 🪙 — 8 100 ⭐", callback_data="buy_star:55500")],
    [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:replenish")],
])