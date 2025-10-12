from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def payments_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Банковская карта", callback_data="pay:card")],
        [InlineKeyboardButton(text="🇷🇺 SberPay | T‑Pay | ЮMoney", callback_data="pay:ru")],
        [InlineKeyboardButton(text="⭐ Звезды", callback_data="pay:stars")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:start")],
    ])


def payments_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Способы оплаты", callback_data="goto:replenish")]
    ])


def ru_bundles_keyboard(bundles: list[tuple[int, int]]) -> InlineKeyboardMarkup:
    icons_map: dict[int, str] = {
        3000: "🎯",
        11000: "🚀",
        24000: "💎",
        38000: "👑",
    }
    bonus_map: dict[int, int] = {
        3000: 0,
        11000: 0,
        24000: 0,
        38000: 0,
    }
    tag_map: dict[int, str] = {
        38000: " 🔥",
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


def card_bundles_keyboard(bundles: list[tuple[int, int]]) -> InlineKeyboardMarkup:
    icons_map: dict[int, str] = {
        3000: "🎯",
        11000: "🚀",
        24000: "💎",
        38000: "👑",
    }
    bonus_map: dict[int, int] = {
        3000: 0,
        11000: 0,
        24000: 0,
        38000: 0,
    }
    tag_map: dict[int, str] = {
        11000: " 🔥",
    }
    rows: list[list[InlineKeyboardButton]] = []
    for tokens, price in bundles:
        icon = icons_map.get(tokens, "🎁")
        bonus = bonus_map.get(tokens, 0)
        bonus_text = f" (+{bonus} 🎁)" if bonus else ""
        tag_text = tag_map.get(tokens, "")
        rows.append([InlineKeyboardButton(text=f"{icon} {tokens} токенов{bonus_text} — {price} ₽{tag_text}", callback_data=f"pay:card:{tokens}")])
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="goto:replenish")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def pay_link_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", url=url)],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:replenish")],
    ])


async def stars_bundles_keyboard(settings_service) -> InlineKeyboardMarkup:
    icons_map: dict[int, str] = {
        3000: "🎯",
        11000: "🚀",
        24000: "💎",
        38000: "👑",
    }
    bonus_map: dict[int, int] = {
        3000: 0,
        11000: 0,
        24000: 0,
        38000: 0,
    }
    tag_map: dict[int, str] = {
        38000: " 🔥",
    }
    
    # Get star prices from settings
    base_tokens_list = [3000, 11000, 24000, 38000]
    rows: list[list[InlineKeyboardButton]] = []
    
    for base_tokens in base_tokens_list:
        try:
            stars = int(await settings_service.get_value(f"{base_tokens}_stars_price"))
        except Exception:
            stars = 0  # fallback if setting not found
        
        icon = icons_map.get(base_tokens, "🎁")
        bonus = bonus_map.get(base_tokens, 0)
        total_tokens = base_tokens + bonus
        bonus_text = f" (+{bonus} 🎁)" if bonus else ""
        tag_text = tag_map.get(base_tokens, "")
        label = f"{icon} {base_tokens} токенов{bonus_text} — {stars} ⭐{tag_text}"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"pay:stars:{total_tokens}:{stars}")])
    
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="goto:replenish")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

