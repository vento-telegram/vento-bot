from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def referral_keyboard(share_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Поделиться своей ссылкой", url=share_url)],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="goto:replenish")],
        ]
    )

