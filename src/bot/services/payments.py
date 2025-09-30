import logging
import base64
import uuid
from typing import Tuple

import aiohttp
from yookassa import Configuration, Payment

from bot.interfaces.services.payments import AbcPaymentsService
from bot.interfaces.uow import AbcUnitOfWork
from bot.enums import LedgerReasonEnum
from bot.entities.ledger import LedgerEntity
from bot.settings import settings


logger = logging.getLogger(__name__)


class PaymentsService(AbcPaymentsService):
    def __init__(self, uow: AbcUnitOfWork):
        self._uow = uow
        if settings.YOOKASSA.SHOP_ID and settings.YOOKASSA.SECRET_KEY:
            Configuration.account_id = settings.YOOKASSA.SHOP_ID
            Configuration.secret_key = settings.YOOKASSA.SECRET_KEY

    async def create_ru_payment(self, user_id: int, tokens: int, price_rub: int) -> str:
        if not (settings.YOOKASSA.SHOP_ID and settings.YOOKASSA.SECRET_KEY):
            raise RuntimeError("YooKassa credentials are not configured")

        payment = Payment.create({
            "amount": {"value": f"{price_rub}.00", "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": "https://t.me"},
            "capture": True,
            "description": f"Vento tokens: {tokens} for user {user_id}",
            "metadata": {"user_id": user_id, "tokens": tokens},
        })
        return payment.confirmation.confirmation_url

    async def check_payment_and_credit(self, payment_id: str) -> bool:
        payment = Payment.find_one(payment_id)
        if payment.status != "succeeded":
            return False
        metadata = payment.metadata or {}
        telegram_id = int(metadata.get("user_id"))
        tokens = int(metadata.get("tokens"))
        async with self._uow:
            user = await self._uow.user.get_by_telegram_id(telegram_id)
            if not user:
                logger.error("User with telegram_id %s not found to credit tokens", telegram_id)
                return False
            updated = await self._uow.user.update_balance_by_user_id(user.id, tokens)
            if updated:
                await self._uow.ledger.add(
                    LedgerEntity(user_id=user.id, delta=tokens, reason=LedgerReasonEnum.purchase_stars)
                )
        return True

    async def create_card_payment(self, user_id: int, tokens: int, amount_minor: int, currency: str) -> str:
        shop_id = settings.BEPAY.SHOP_ID
        secret = settings.BEPAY.SECRET_KEY
        if not (shop_id and secret):
            raise RuntimeError("bePaid credentials are not configured")
        if not amount_minor or amount_minor <= 0:
            raise RuntimeError("bePaid amount is not configured (minor units <= 0)")

        request_id = str(uuid.uuid4())
        auth_bytes = f"{shop_id}:{secret}".encode()
        auth_header = base64.b64encode(auth_bytes).decode()

        # Build checkout payload (bePaid Checkout)
        callback_base = settings.BEPAY.CALLBACK_BASE.rstrip('/')
        payload = {
            "checkout": {
                "version": 2,
                "test": bool(settings.BEPAY.TEST),
                "transaction_type": "payment",
                "attempts": 3,
                "order": {
                    "amount": int(amount_minor),
                    "currency": (currency or "USD").upper(),
                    "description": f"Vento tokens: {tokens} for user {user_id}",
                    "tracking_id": f"tokens:{tokens}:user:{user_id}",
                },
                "settings": {
                    "success_url": f"{callback_base}/webhooks/bepaid?status=success",
                    "fail_url": f"{callback_base}/webhooks/bepaid?status=fail",
                    "decline_url": f"{callback_base}/webhooks/bepaid?status=decline",
                    "cancel_url": f"{callback_base}/webhooks/bepaid?status=cancel",
                    "notification_url": f"{callback_base}/webhooks/bepaid",
                    "language": "ru",
                },
                # Customer fields left minimal to reduce friction in widget
            }
        }

        url = f"{settings.BEPAY.API_BASE}/checkout"
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "RequestID": request_id,
        }
        logger.debug(
            "bePaid create checkout: user_id=%s tokens=%s amount_minor=%s currency=%s request_id=%s",
            user_id, tokens, amount_minor, currency, request_id,
        )
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    text = await resp.text()
                    if resp.status != 200:
                        logger.error("bePaid checkout error status=%s body=%s", resp.status, text)
                        raise RuntimeError("Failed to create bePaid checkout token")
                    try:
                        data = await resp.json()
                    except Exception:
                        logger.error("bePaid non-JSON response: %s", text)
                        raise RuntimeError("Invalid bePaid response")

                    obj = data.get("checkout") or data
                    redirect = obj.get("redirect_url") or data.get("redirect_url")
                    if not redirect:
                        token = obj.get("token") or data.get("token")
                        if token:
                            redirect = f"{settings.BEPAY.CHECKOUT_BASE}/v2/confirm_order/{token}"
                    if not redirect:
                        logger.error("bePaid response missing redirect_url and token: %s", data)
                        raise RuntimeError("bePaid did not return redirect_url")
                    return redirect
        except Exception:
            logger.exception("bePaid checkout request failed")
            raise

    async def process_bepaid_webhook(self, payload: dict) -> Tuple[bool, int | None, int | None]:
        try:
            tx = payload.get("transaction") or {}
            status = (tx.get("status") or "").lower()
            type_ = (tx.get("type") or "").lower()
            if type_ == "payment" and status == "successful":
                tracking_id = tx.get("tracking_id") or ""
                # tracking_id format: tokens:{tokens}:user:{telegram_id}
                tokens: int | None = None
                tel_id: int | None = None
                try:
                    parts = tracking_id.split(":")
                    # expecting ["tokens", <tokens>, "user", <id>]
                    for i in range(len(parts) - 1):
                        if parts[i] == "tokens":
                            tokens = int(parts[i + 1])
                        if parts[i] == "user":
                            tel_id = int(parts[i + 1])
                except Exception:
                    tokens = None
                    tel_id = None
                if not (tokens and tel_id):
                    return False, None, None
                async with self._uow:
                    user = await self._uow.user.get_by_telegram_id(tel_id)
                    if not user:
                        logger.error("User with telegram_id %s not found to credit tokens (bePaid)", tel_id)
                        return False, tel_id, tokens
                    updated = await self._uow.user.update_balance_by_user_id(user.id, int(tokens))
                    if updated:
                        await self._uow.ledger.add(
                            LedgerEntity(user_id=user.id, delta=int(tokens), reason=LedgerReasonEnum.purchase_stars)
                        )
                return True, tel_id, tokens
            # Handle async task status pings gracefully
            return True, None, None
        except Exception:
            logger.exception("bePaid webhook processing error")
            return False, None, None

