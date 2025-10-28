from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def referral_keyboard(share_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Поделиться", url=share_url)],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="referral:stats")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="goto:replenish")],
        ]
    )


def referral_bonus_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Выбрать ИИ", callback_data="goto:switch")],
        ]
    )

