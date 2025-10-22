import logging
from typing import List

from aiogram import F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from dependency_injector.wiring import Provide, inject

from bot.container import Container
from bot.enums import TransactionReasonEnum
from bot.handlers.admin import router as admin_router, _ensure_admin, AdminStates
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
    await message.answer("ÐÐ´Ð¼Ð¸Ð½-Ð¼ÐµÐ½ÑŽ:", reply_markup=admin_main_keyboard())


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
        await call.message.edit_text("ÐÐ´Ð¼Ð¸Ð½-Ð¼ÐµÐ½ÑŽ:", reply_markup=admin_main_keyboard())
    except Exception:
        await call.message.answer("ÐÐ´Ð¼Ð¸Ð½-Ð¼ÐµÐ½ÑŽ:", reply_markup=admin_main_keyboard())
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

    lines: list[str] = ["Ð’Ñ‹Ñ€ÑƒÑ‡ÐºÐ° Ð·Ð° ÑÐµÐ³Ð¾Ð´Ð½Ñ:"]
    if stars_total:
        lines.append(f"â€¢ Ð—Ð²ÐµÐ·Ð´Ñ‹: {stars_total} â­")
    if rub_total:
        lines.append(f"â€¢ Ð ÑƒÐ±Ð»Ð¸: {rub_total} â‚½")
    if sub_stars_total or sub_rub_total or sub_byn_total:
        lines.append("â€¢ ÐŸÐ¾Ð´Ð¿Ð¸ÑÐºÐ¸:")
        if sub_stars_total:
            lines.append(f"  â€“ Stars: {sub_stars_total} XTR")
        if sub_rub_total:
            lines.append(f"  â€“ RUB: {sub_rub_total} â‚½")
        if sub_byn_total:
            lines.append(f"  â€“ BYN: {sub_byn_total} BYN")

    if len(lines) == 1:
        lines.append("Ð¡ÐµÐ³Ð¾Ð´Ð½Ñ Ð¿Ð¾ÐºÑƒÐ¿Ð¾Ðº Ð½Ðµ Ð±Ñ‹Ð»Ð¾.")

    text = "\n".join(lines)
    try:
        await call.message.edit_text(text, reply_markup=admin_back_keyboard())
    except Exception:
        await call.message.answer(text, reply_markup=admin_back_keyboard())
    await call.answer()


@admin_router.callback_query(F.data == "admin:earnings_by_date")
@inject
async def earnings_by_date_prompt(
    call: CallbackQuery,
    state: FSMContext,
    user_service: AbcUserService = Provide[Container.user_service],
):
    exists, is_admin = await _ensure_admin(user_service, call.from_user.id)
    if not exists or not is_admin:
        await call.answer()
        return
    await state.set_state(AdminStates.earnings_by_date)
    text = "Ð’Ð²ÐµÐ´Ð¸Ñ‚Ðµ Ð´Ð°Ñ‚Ñƒ Ð² Ñ„Ð¾Ñ€Ð¼Ð°Ñ‚Ðµ Ð´Ð´.Ð¼Ð¼.Ð³Ð³Ð³Ð³"
    try:
        await call.message.edit_text(text, reply_markup=admin_back_keyboard())
    except Exception:
        await call.message.answer(text, reply_markup=admin_back_keyboard())
    await call.answer()


@admin_router.message(AdminStates.earnings_by_date)
@inject
async def earnings_by_date_handle(
    message: Message,
    state: FSMContext,
    uow: AbcUnitOfWork = Provide[Container.uow],
    settings: AbcSettingsService = Provide[Container.settings_service],
    user_service: AbcUserService = Provide[Container.user_service],
):
    exists, is_admin = await _ensure_admin(user_service, message.from_user.id)
    if not exists or not is_admin:
        await message.answer("ÐÐµÐ´Ð¾ÑÑ‚Ð°Ñ‚Ð¾Ñ‡Ð½Ð¾ Ð¿Ñ€Ð°Ð²")
        await state.clear()
        return

    raw = (message.text or "").strip()
    from datetime import datetime
    try:
        day = datetime.strptime(raw, "%d.%m.%Y").date()
    except Exception:
        await message.answer("ÐÐµÐ²ÐµÑ€Ð½Ñ‹Ð¹ Ñ„Ð¾Ñ€Ð¼Ð°Ñ‚ Ð´Ð°Ñ‚Ñ‹. Ð’Ð²ÐµÐ´Ð¸Ñ‚Ðµ Ð² Ñ„Ð¾Ñ€Ð¼Ð°Ñ‚Ðµ Ð´Ð´.Ð¼Ð¼.Ð³Ð³Ð³Ð³")
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
        txs = await uow.transaction.list_by_date_by_reasons(day, reasons)

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

    pretty_date = day.strftime("%d.%m.%Y")
    lines: list[str] = [f"Ð’Ñ‹Ñ€ÑƒÑ‡ÐºÐ° Ð·Ð° {pretty_date}:"]
    if stars_total:
        lines.append(f"â€¢ Stars: {stars_total} XTR")
    if rub_total:
        lines.append(f"â€¢ RUB: {rub_total} â‚½")
    if sub_stars_total or sub_rub_total or sub_byn_total:
        lines.append("â€¢ ÐŸÐ¾Ð´Ð¿Ð¸ÑÐºÐ¸:")
        if sub_stars_total:
            lines.append(f"  - Stars: {sub_stars_total} XTR")
        if sub_rub_total:
            lines.append(f"  - RUB: {sub_rub_total} â‚½")
        if sub_byn_total:
            lines.append(f"  - BYN: {sub_byn_total} BYN")

    if len(lines) == 1:
        lines.append("ÐŸÐ¾ÐºÑƒÐ¿Ð¾Ðº Ð½Ðµ Ð±Ñ‹Ð»Ð¾.")

    await state.clear()
    await message.answer("\n".join(lines), reply_markup=admin_back_keyboard())


@admin_router.callback_query(F.data == "admin:users_total")
@inject
async def users_total(
    call: CallbackQuery,
    uow: AbcUnitOfWork = Provide[Container.uow],
    user_service: AbcUserService = Provide[Container.user_service],
):
    exists, is_admin = await _ensure_admin(user_service, call.from_user.id)
    if not exists or not is_admin:
        await call.answer()
        return
    async with uow:
        count = await uow.user.count_all()
    text = f"ÐžÐ±Ñ‰ÐµÐµ ÐºÐ¾Ð»Ð¸Ñ‡ÐµÑÑ‚Ð²Ð¾ Ð¿Ð¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ñ‚ÐµÐ»ÐµÐ¹: {count}"
    try:
        await call.message.edit_text(text, reply_markup=admin_back_keyboard())
    except Exception:
        await call.message.answer(text, reply_markup=admin_back_keyboard())
    await call.answer()


@admin_router.callback_query(F.data == "admin:users_today")
@inject
async def users_today(
    call: CallbackQuery,
    uow: AbcUnitOfWork = Provide[Container.uow],
    user_service: AbcUserService = Provide[Container.user_service],
):
    exists, is_admin = await _ensure_admin(user_service, call.from_user.id)
    if not exists or not is_admin:
        await call.answer()
        return
    async with uow:
        count = await uow.user.count_today()
    text = f"ÐšÐ¾Ð»Ð¸Ñ‡ÐµÑÑ‚Ð²Ð¾ Ð¿Ð¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ñ‚ÐµÐ»ÐµÐ¹ Ð·Ð° ÑÐµÐ³Ð¾Ð´Ð½Ñ: {count}"
    try:
        await call.message.edit_text(text, reply_markup=admin_back_keyboard())
    except Exception:
        await call.message.answer(text, reply_markup=admin_back_keyboard())
    await call.answer()



@admin_router.callback_query(F.data == "admin:active_today")
@inject
async def active_today(
    call: CallbackQuery,
    uow: AbcUnitOfWork = Provide[Container.uow],
    user_service: AbcUserService = Provide[Container.user_service],
):
    exists, is_admin = await _ensure_admin(user_service, call.from_user.id)
    if not exists or not is_admin:
        await call.answer()
        return
    async with uow:
        count = await uow.transaction.count_active_users_today()
    text = f"Актив за сегодня: {count}"
    try:
        await call.message.edit_text(text, reply_markup=admin_back_keyboard())
    except Exception:
        await call.message.answer(text, reply_markup=admin_back_keyboard())
    await call.answer()
@admin_router.callback_query(F.data == "admin:users_by_date")
@inject
async def users_by_date_prompt(
    call: CallbackQuery,
    state: FSMContext,
    user_service: AbcUserService = Provide[Container.user_service],
):
    exists, is_admin = await _ensure_admin(user_service, call.from_user.id)
    if not exists or not is_admin:
        await call.answer()
        return
    await state.set_state(AdminStates.users_by_date)
    text = "Ð’Ð²ÐµÐ´Ð¸Ñ‚Ðµ Ð´Ð°Ñ‚Ñƒ Ð² Ñ„Ð¾Ñ€Ð¼Ð°Ñ‚Ðµ Ð´Ð´.Ð¼Ð¼.Ð³Ð³Ð³Ð³"
    try:
        await call.message.edit_text(text, reply_markup=admin_back_keyboard())
    except Exception:
        await call.message.answer(text, reply_markup=admin_back_keyboard())
    await call.answer()


@admin_router.message(AdminStates.users_by_date)
@inject
async def users_by_date_handle(
    message: Message,
    state: FSMContext,
    uow: AbcUnitOfWork = Provide[Container.uow],
    user_service: AbcUserService = Provide[Container.user_service],
):
    exists, is_admin = await _ensure_admin(user_service, message.from_user.id)
    if not exists or not is_admin:
        await message.answer("ÐÐµÐ´Ð¾ÑÑ‚Ð°Ñ‚Ð¾Ñ‡Ð½Ð¾ Ð¿Ñ€Ð°Ð²")
        await state.clear()
        return
    raw = (message.text or "").strip()
    from datetime import datetime
    try:
        day = datetime.strptime(raw, "%d.%m.%Y").date()
    except Exception:
        await message.answer("ÐÐµÐ²ÐµÑ€Ð½Ñ‹Ð¹ Ñ„Ð¾Ñ€Ð¼Ð°Ñ‚ Ð´Ð°Ñ‚Ñ‹. Ð’Ð²ÐµÐ´Ð¸Ñ‚Ðµ Ð² Ñ„Ð¾Ñ€Ð¼Ð°Ñ‚Ðµ Ð´Ð´.Ð¼Ð¼.Ð³Ð³Ð³Ð³")
        return
    async with uow:
        count = await uow.user.count_by_date(day)
    pretty_date = day.strftime("%d.%m.%Y")
    text = f"ÐšÐ¾Ð»Ð¸Ñ‡ÐµÑÑ‚Ð²Ð¾ Ð¿Ð¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ñ‚ÐµÐ»ÐµÐ¹ Ð·Ð° {pretty_date}: {count}"
    await state.clear()
    await message.answer(text, reply_markup=admin_back_keyboard())
