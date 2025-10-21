from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def payments_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌍 Картой МИР", callback_data="pay:card")],
        [InlineKeyboardButton(text="🚀 Visa • Mastercard", callback_data="pay:card_byn")],
        [InlineKeyboardButton(text="🇷🇺 SberPay • T‑Pay • ЮMoney", callback_data="pay:ru")],
        [InlineKeyboardButton(text="⭐ Звезды", callback_data="pay:stars")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:start")],
    ])


def card_byn_bundles_keyboard(bundles: list[tuple[int, int]], usd_rate: float, has_subscription: bool = False) -> InlineKeyboardMarkup:
    icons_map: dict[int, str] = {
        300: "🎯",
        1100: "🚀",
        2400: "💎",
        3800: "👑",
        7000: "🛸",
    }
    bonus_map: dict[int, int] = {
        300: 0,
        1100: 0,
        2400: 0,
        3800: 0,
        7000: 0,
    }
    tag_map: dict[int, str] = {
        2400: " 🔥",
    }
    rows: list[list[InlineKeyboardButton]] = []
    # Add subscription option on top
    for tokens, byn in bundles:
        icon = icons_map.get(tokens, "💠")
        bonus = bonus_map.get(tokens, 0)
        bonus_text = f" (+{bonus} 🔹)" if bonus else ""
        tag_text = tag_map.get(tokens, "")
        try:
            usd = byn / float(usd_rate) if usd_rate else 0
        except Exception:
            usd = 0
        # Use ~ and 2 decimals for USD approximation
        usd_text = f" (~${usd:.2f})" if usd > 0 else ""
        if tokens in (1100, 2400, 3800, 7000):
            rows.append([
                InlineKeyboardButton(
                    text=f"{icon} {tokens} токенов{bonus_text} + 🎁 Гайд — {byn} BYN{usd_text}{tag_text}",
                    callback_data=f"pay:card_byn:{tokens}",
                )
            ])
        else:
            rows.append([
                InlineKeyboardButton(
                    text=f"{icon} {tokens} токенов{bonus_text} — {byn} BYN{usd_text}{tag_text}",
                    callback_data=f"pay:card_byn:{tokens}",
                )
            ])
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="goto:replenish")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def payments_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Способы оплаты", callback_data="goto:replenish")]
    ])


def ru_bundles_keyboard(bundles: list[tuple[int, int]], has_subscription: bool = False) -> InlineKeyboardMarkup:
    icons_map: dict[int, str] = {
        300: "🎯",
        1100: "🚀",
        2400: "💎",
        3800: "👑",
        7000: "🛸",
    }
    bonus_map: dict[int, int] = {
        300: 0,
        1100: 0,
        2400: 0,
        3800: 0,
        7000: 0,
    }
    tag_map: dict[int, str] = {
        2400: " 🔥",
    }
    rows: list[list[InlineKeyboardButton]] = []
    # Add subscription option on top
    for tokens, price in bundles:
        icon = icons_map.get(tokens, "🎁")
        bonus = bonus_map.get(tokens, 0)
        bonus_text = f" (+{bonus} 🎁)" if bonus else ""
        tag_text = tag_map.get(tokens, "")
        if tokens in (1100, 2400, 3800, 7000):
            rows.append([InlineKeyboardButton(text=f"{icon} {tokens} токенов{bonus_text} + 🎁 Гайд — {price} ₽{tag_text}", callback_data=f"pay:ru:{tokens}")])
        else:
            rows.append([InlineKeyboardButton(text=f"{icon} {tokens} токенов{bonus_text} — {price} ₽{tag_text}", callback_data=f"pay:ru:{tokens}")])
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="goto:replenish")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def ru_bundles_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:replenish")],
    ])


def card_bundles_keyboard(bundles: list[tuple[int, int]], has_subscription: bool = False) -> InlineKeyboardMarkup:
    icons_map: dict[int, str] = {
        300: "🎯",
        1100: "🚀",
        2400: "💎",
        3800: "👑",
        7000: "🛸",
    }
    bonus_map: dict[int, int] = {
        300: 0,
        1100: 0,
        2400: 0,
        3800: 0,
        7000: 0,
    }
    tag_map: dict[int, str] = {
        2400: " 🔥",
    }
    rows: list[list[InlineKeyboardButton]] = []
    for tokens, price in bundles:
        icon = icons_map.get(tokens, "🎁")
        bonus = bonus_map.get(tokens, 0)
        bonus_text = f" (+{bonus} 🎁)" if bonus else ""
        tag_text = tag_map.get(tokens, "")
        if tokens in (1100, 2400, 3800, 7000):
            rows.append([InlineKeyboardButton(text=f"{icon} {tokens} токенов{bonus_text} + 🎁 Гайд — {price} ₽{tag_text}", callback_data=f"pay:card:{tokens}")])
        else:
            rows.append([InlineKeyboardButton(text=f"{icon} {tokens} токенов{bonus_text} — {price} ₽{tag_text}",
                                              callback_data=f"pay:card:{tokens}")])
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="goto:replenish")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def pay_link_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", url=url)],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:replenish")],
    ])


async def stars_bundles_keyboard(settings_service, has_subscription: bool = False) -> InlineKeyboardMarkup:
    icons_map: dict[int, str] = {
        300: "🎯",
        1100: "🚀",
        2400: "💎",
        3800: "👑",
        7000: "🛸",
    }
    bonus_map: dict[int, int] = {
        300: 0,
        1100: 0,
        2400: 0,
        3800: 0,
        7000: 0,
    }
    tag_map: dict[int, str] = {
        2400: " 🔥",
    }
    
    # Get star prices from settings
    base_tokens_list = [300, 1100, 2400, 3800, 7000]
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
        if base_tokens in (1100, 2400, 3800, 7000):
            label = f"{icon} {base_tokens} токенов{bonus_text} — 🎁 Гайд {stars} ⭐{tag_text}"
        else:
            label = f"{icon} {base_tokens} токенов{bonus_text} — {stars} ⭐{tag_text}"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"pay:stars:{total_tokens}:{stars}")])
    
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="goto:replenish")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

