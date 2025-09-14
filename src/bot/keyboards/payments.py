from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def payments_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 SberPay | T‑Pay | ЮMoney", callback_data="pay:ru")],
        [InlineKeyboardButton(text="⭐ Звезды", callback_data="pay:stars")],
        [InlineKeyboardButton(text="🪙 Крипта", callback_data="pay:crypto")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:account")],
    ])


def payments_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Способы оплаты", callback_data="goto:replenish")]
    ])


def ru_bundles_keyboard(bundles: list[tuple[int, int]]) -> InlineKeyboardMarkup:
    icons_map: dict[int, str] = {
        700: "🐣",
        1600: "🎯",
        4500: "👑",
        11000: "💎",
        28000: "🚀",
    }
    bonus_map: dict[int, int] = {
        700: 0,
        1600: 200,
        4500: 900,
        11000: 2100,
        28000: 8000,
    }
    tag_map: dict[int, str] = {
        4500: " 🔥",
    }
    rows: list[list[InlineKeyboardButton]] = []
    for tokens, price in bundles:
        icon = icons_map.get(tokens, "🎁")
        bonus = bonus_map.get(tokens, 0)
        bonus_text = f" (+{bonus} 🎁)" if bonus else ""
        tag_text = tag_map.get(tokens, "")
        rows.append([InlineKeyboardButton(text=f"{icon} {tokens} токенов{bonus_text} — {price} ₽{tag_text}", callback_data=f"pay:ru:{tokens}")])
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="goto:replenish")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def ru_bundles_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:replenish")],
    ])


