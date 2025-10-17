import logging
from typing import List

from aiogram import F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from dependency_injector.wiring import Provide, inject

from bot.container import Container
from bot.enums import TransactionReasonEnum
from bot.handlers.admin import router as admin_router, _ensure_admin
from bot.interfaces.services.settings import AbcSettingsService
from bot.interfaces.services.user import AbcUserService
from bot.interfaces.uow import AbcUnitOfWork
from bot.keyboards.admin import admin_back_keyboard, admin_main_keyboard

logger = logging.getLogger(__name__)


@admin_router.message(Command("start"))
@inject
async def admin_start(
    message: Message,
    user_service: AbcUserService = Provide[Container.user_service],
):
    exists, is_admin = await _ensure_admin(user_service, message.from_user.id)
    if not exists or not is_admin:
        return
    await message.answer("Админ-меню:", reply_markup=admin_main_keyboard())


@admin_router.callback_query(F.data == "goto:admin")
@inject
async def goto_admin(
    call: CallbackQuery,
    user_service: AbcUserService = Provide[Container.user_service],
):
    exists, is_admin = await _ensure_admin(user_service, call.from_user.id)
    if not exists or not is_admin:
        await call.answer()
        return
    try:
        await call.message.edit_text("Админ-меню:", reply_markup=admin_main_keyboard())
    except Exception:
        await call.message.answer("Админ-меню:", reply_markup=admin_main_keyboard())
    await call.answer()


@admin_router.callback_query(F.data == "admin:earnings_today")
@inject
async def earnings_today(
    call: CallbackQuery,
    uow: AbcUnitOfWork = Provide[Container.uow],
    settings: AbcSettingsService = Provide[Container.settings_service],
    user_service: AbcUserService = Provide[Container.user_service],
):
    exists, is_admin = await _ensure_admin(user_service, call.from_user.id)
    if not exists or not is_admin:
        await call.answer()
        return

    reasons: List[str] = [
        str(TransactionReasonEnum.purchase_stars),
        str(TransactionReasonEnum.purchase_bepaid),
        str(TransactionReasonEnum.purchase_yookassa),
        str(TransactionReasonEnum.purchase_subscription_stars),
        str(TransactionReasonEnum.purchase_subscription_bepaid),
        str(TransactionReasonEnum.purchase_subscription_yookassa),
        str(TransactionReasonEnum.purchase_subscription_bonus),
    ]
    stars_total = 0
    rub_total = 0
    sub_stars_total = 0
    sub_rub_total = 0
    sub_byn_total = 0

    async with uow:
        txs = await uow.transaction.list_today_by_reasons(reasons)

    async def _get_int(key: str) -> int:
        try:
            val = await settings.get_value(key)
            return int(val) if val is not None else 0
        except Exception:
            return 0

    for tx in txs:
        reason = str(tx.reason)
        tokens = int(getattr(tx, "delta", 0) or 0)
        if reason == str(TransactionReasonEnum.purchase_stars):
            stars_total += await _get_int(f"{tokens}_stars_price")
        elif reason == str(TransactionReasonEnum.purchase_yookassa):
            rub_total += await _get_int(f"{tokens}_bundle_price")
        elif reason == str(TransactionReasonEnum.purchase_bepaid):
            rub_total += await _get_int(f"{tokens}_bundle_price")
        elif reason == str(TransactionReasonEnum.purchase_subscription_stars):
            price = await _get_int("subscription_stars_price")
            sub_stars_total += price if price > 0 else 2999
        elif reason in (
            str(TransactionReasonEnum.purchase_subscription_yookassa),
            str(TransactionReasonEnum.purchase_subscription_bepaid),
        ):
            rub_price = await _get_int("subscription_rub_price")
            sub_rub_total += rub_price if rub_price > 0 else 2999
        elif reason == str(TransactionReasonEnum.purchase_subscription_bonus):
            rub_price = await _get_int("subscription_rub_price")
            sub_rub_total += rub_price if rub_price > 0 else 2999

    lines: list[str] = ["Выручка за сегодня:"]
    if stars_total:
        lines.append(f"• Звезды: {stars_total} ⭐")
    if rub_total:
        lines.append(f"• Рубли: {rub_total} ₽")
    if sub_stars_total or sub_rub_total or sub_byn_total:
        lines.append("• Подписки:")
        if sub_stars_total:
            lines.append(f"  – Stars: {sub_stars_total} XTR")
        if sub_rub_total:
            lines.append(f"  – RUB: {sub_rub_total} ₽")
        if sub_byn_total:
            lines.append(f"  – BYN: {sub_byn_total} BYN")

    if len(lines) == 1:
        lines.append("Сегодня покупок не было.")

    text = "\n".join(lines)
    try:
        await call.message.edit_text(text, reply_markup=admin_back_keyboard())
    except Exception:
        await call.message.answer(text, reply_markup=admin_back_keyboard())
    await call.answer()
