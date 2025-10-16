from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def payments_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌍 Картой МИР", callback_data="pay:card")],
        [InlineKeyboardButton(text="🚀 Картой VISA | Mastercard", callback_data="pay:card_byn")],
        [InlineKeyboardButton(text="🇷🇺 SberPay | T‑Pay | ЮMoney", callback_data="pay:ru")],
        [InlineKeyboardButton(text="⭐ Звезды", callback_data="pay:stars")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:start")],
    ])


def payments_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Способы оплаты", callback_data="goto:replenish")]
    ])


def ru_bundles_keyboard(bundles: list[tuple[int, int]]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for tokens, price in bundles:
        guide_text = " + 🎁 Гайд" if tokens == 7000 else ""
        icon = "🛸" if tokens == 7000 else "🪙"
        label = f"{icon} {tokens} токенов{guide_text} — {price} ₽"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"pay:ru:{tokens}")])
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="goto:replenish")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def ru_bundles_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:replenish")],
    ])


def card_bundles_keyboard(bundles: list[tuple[int, int]]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for tokens, price in bundles:
        guide_text = " + 🎁 Гайд" if tokens == 7000 else ""
        icon = "🛸" if tokens == 7000 else "🪙"
        label = f"{icon} {tokens} токенов{guide_text} — {price} ₽"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"pay:card:{tokens}")])
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="goto:replenish")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def card_byn_bundles_keyboard(bundles: list[tuple[int, int]], usd_rate: float) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for tokens, byn in bundles:
        guide_text = " + 🎁 Гайд" if tokens == 7000 else ""
        icon = "🛸" if tokens == 7000 else "🪙"
        try:
            usd = byn / float(usd_rate) if usd_rate else 0.0
        except Exception:
            usd = 0.0
        usd_text = f" (~${usd:.2f})" if usd > 0 else ""
        label = f"{icon} {tokens} токенов{guide_text} — {byn} BYN{usd_text}"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"pay:card_byn:{tokens}")])
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="goto:replenish")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def pay_link_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", url=url)],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:replenish")],
    ])


async def stars_bundles_keyboard(settings_service) -> InlineKeyboardMarkup:
    base_tokens_list = [300, 1100, 2400, 3800, 7000]
    rows: list[list[InlineKeyboardButton]] = []
    for base_tokens in base_tokens_list:
        try:
            stars = int(await settings_service.get_value(f"{base_tokens}_stars_price"))
        except Exception:
            stars = 0  # fallback if setting not found

        guide_text = " + 🎁 Гайд" if base_tokens == 7000 else ""
        icon = "🛸" if base_tokens == 7000 else "🪙"
        label = f"{icon} {base_tokens} токенов{guide_text} — {stars} ⭐"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"pay:stars:{base_tokens}:{stars}")])

    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="goto:replenish")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

