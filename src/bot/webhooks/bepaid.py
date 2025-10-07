from aiogram import Bot
from aiohttp import web
import json
import logging

from dependency_injector.wiring import inject, Provide

from bot.container import Container
from bot.enums import LedgerReasonEnum, BotModeEnum
from bot.interfaces.services import AbcUserService
from bot.keyboards import start_keyboard

logger = logging.getLogger(__name__)

@inject
async def bepaid_handle(
    request: web.Request,
    bot: Bot = Provide[Container.bot],
    user_service: AbcUserService = Provide[Container.user_service],
):
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"status": "bad json"}, status=400)

    try:
        logger.info(
            "bepaid_webhook payload=%s", json.dumps(body, ensure_ascii=False)
        )
    except Exception:
        logger.info("bepaid_webhook payload=(non-json)")

    def _extract_status_and_tracking(
            payload: dict,
    ) -> tuple[str | None, str | None]:
        status_candidates: list[str | None] = []
        tracking_candidates: list[str | None] = []

        checkout = payload.get("checkout")
        if isinstance(checkout, dict):
            status_candidates.append(
                checkout.get("status") or checkout.get("state")
            )
            order = checkout.get("order") or {}
            if isinstance(order, dict):
                tracking_candidates.append(order.get("tracking_id"))

        transaction = payload.get("transaction")
        if isinstance(transaction, dict):
            status_candidates.append(transaction.get("status"))
            payment = transaction.get("payment") or {}
            if isinstance(payment, dict):
                status_candidates.append(payment.get("status"))
            tracking_candidates.append(transaction.get("tracking_id"))
            order = transaction.get("order") or {}
            if isinstance(order, dict):
                tracking_candidates.append(order.get("tracking_id"))

        status_candidates.append(payload.get("status"))
        tracking_candidates.append(payload.get("tracking_id"))

        status_val = next(
            (s for s in status_candidates if isinstance(s, str) and s), None
        )
        tracking_val = next(
            (t for t in tracking_candidates if isinstance(t, str) and t), None
        )
        return status_val, tracking_val

    status, tracking_id = _extract_status_and_tracking(body)
    telegram_id: int | None = None
    tokens: int | None = None
    try:
        parts = str(tracking_id or "").split(":", maxsplit=1)
        if parts and parts[0].isdigit():
            telegram_id = int(parts[0])
        if len(parts) >= 2 and parts[1].isdigit():
            tokens = int(parts[1])
    except Exception:
        telegram_id = None
        tokens = None

    if not (telegram_id and tokens and tokens > 0):
        logger.warning(
            "bepaid_webhook missing identifiers: status=%s tracking_id=%s",
            status,
            tracking_id,
        )
        return web.json_response({"ok": True})

    status_norm = str(status or "").lower()
    success_statuses = {"successful", "succeeded", "paid", "success", "completed"}
    if status_norm not in success_statuses:
        logger.info(
            "bepaid_webhook non-final status: %s (tracking_id=%s)",
            status_norm,
            tracking_id,
        )
        return web.json_response({"ok": True})

    try:
        await user_service.add_tokens_by_telegram_id(
            telegram_id=telegram_id,
            amount=int(tokens),
            reason=LedgerReasonEnum.purchase_stars,
        )
    except Exception:
        logger.exception(
            "bepaid_webhook credit_failed user=%s tokens=%s", telegram_id, tokens
        )

    try:
        user = await user_service.get_user(telegram_id)
        balance = user.balance if user else None
        balance_text = f"*{balance}*" if balance is not None else "обновлён"
        await bot.send_message(
            telegram_id,
            text=(
                f"✅ Оплата прошла успешно! Зачислено {tokens} токенов.\n\n"
                f"🪙 Твой баланс: {balance_text} токенов\n\n"
                "👇 Что хочешь сделать?"
            ),
            reply_markup=start_keyboard(BotModeEnum.passive),
        )
    except Exception:
        logger.exception("bepaid_webhook notify_failed user=%s", telegram_id)

    return web.json_response({"ok": True})
