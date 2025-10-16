from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.enums import BotModeEnum


def start_keyboard(current_mode: BotModeEnum) -> InlineKeyboardMarkup:
    switch_label = "👾 Выбрать ИИ" if current_mode == BotModeEnum.passive else "👾 Сменить ИИ"
    buttons: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="🎟️ Баланс и подписка", callback_data="goto:replenish")],
        [InlineKeyboardButton(text=switch_label, callback_data="goto:switch")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

