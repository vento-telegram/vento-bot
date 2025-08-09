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
    [InlineKeyboardButton(text="5 500 🪙 — 500 ₽ (бонус +500 🪙)", callback_data="buy:5500")],
    [InlineKeyboardButton(text="12 000 🪙 — 1 000 ₽ (бонус +2 000 🪙)", callback_data="buy:12000")],
    [InlineKeyboardButton(text="32 500 🪙 — 2 500 ₽ (бонус +7 500 🪙)", callback_data="buy:32500")],
    [InlineKeyboardButton(text="70 000 🪙 — 5 000 ₽ (бонус +20 000 🪙)", callback_data="buy:70000")],
    [InlineKeyboardButton(text="⭐ Оплатить звёздами", callback_data="goto:replenish_stars")],
    [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:account")],
])


replenish_stars_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="1 000 🪙 — 100 ⭐", callback_data="buy_star:1000")],
    [InlineKeyboardButton(text="5 500 🪙 — 500 ⭐ (бонус +500 🪙)", callback_data="buy_star:5500")],
    [InlineKeyboardButton(text="12 000 🪙 — 1 000 ⭐ (бонус +2 000 🪙)", callback_data="buy_star:12000")],
    [InlineKeyboardButton(text="32 500 🪙 — 2 500 ⭐ (бонус +7 500 🪙)", callback_data="buy_star:32500")],
    [InlineKeyboardButton(text="70 000 🪙 — 5 000 ⭐ (бонус +20 000 🪙)", callback_data="buy_star:70000")],
    [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:replenish")],
])