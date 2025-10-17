import base64
import json
import logging
from typing import Any

import aiohttp
from yookassa import Configuration, Payment

from bot.entities.transaction import TransactionEntity
from bot.enums import TransactionReasonEnum
from bot.interfaces.services.payments import AbcPaymentsService
from bot.interfaces.uow import AbcUnitOfWork
from bot.settings import settings

logger = logging.getLogger(__name__)


class PaymentsService(AbcPaymentsService):
    def __init__(self, uow: AbcUnitOfWork):
        self._uow = uow
        if settings.YOOKASSA.SHOP_ID and settings.YOOKASSA.SECRET_KEY:
            Configuration.account_id = settings.YOOKASSA.SHOP_ID
            Configuration.secret_key = settings.YOOKASSA.SECRET_KEY
        # Prepare BePaid auth header if configured
        self._bepaid_auth: str | None = None
        try:
            shop_id = settings.BEPAID.SHOP_ID or ""
            token = settings.BEPAID.TOKEN or ""
            if shop_id and token:
                creds = f"{shop_id}:{token}".encode()
                self._bepaid_auth = base64.b64encode(creds).decode()
        except Exception:
            self._bepaid_auth = None

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
                await self._uow.transaction.add(
                    TransactionEntity(user_id=user.id, delta=tokens, reason=TransactionReasonEnum.purchase_yookassa)
                )
        return True

    async def create_card_payment(self, user_id: int, tokens: int, price_rub: int) -> str:
        if not self._bepaid_auth:
            raise RuntimeError("BePaid credentials are not configured")

        payload: dict[str, Any] = {
            "checkout": {
                "transaction_type": "payment",
                "order": {
                    "amount": int(price_rub) * 100,
                    "currency": "RUB",
                    "description": f"Vento tokens: {tokens} for user {user_id}",
                    "tracking_id": f"{user_id}:{tokens}",
                },
                "customer": {
                    "first_name": str(user_id),
                },
                "settings": {
                    "notification_url": f"{settings.WEBHOOKS.BASE_URL}/webhooks/bepaid",
                    "success_url": "https://t.me/vento_toolbot",
                    "decline_url": "https://t.me/vento_toolbot",
                    "fail_url": "https://t.me/vento_toolbot",
                    "cancel_url": "https://t.me/vento_toolbot",
                    "language": "ru",
                },
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Version": "2",
            "Authorization": f"Basic {self._bepaid_auth}",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://checkout.bepaid.by/ctp/api/checkouts",
                data=json.dumps(payload),
                headers=headers,
            ) as resp:
                data = await resp.json(content_type=None)
                if resp.status not in {200, 201}:
                    raise RuntimeError(f"BePaid error {resp.status}: {data}")
                # Try common fields for redirect URL
                checkout = data.get("checkout") if isinstance(data, dict) else None
                if isinstance(checkout, dict):
                    url = (
                        checkout.get("redirect_url")
                        or checkout.get("redirect_to")
                        or checkout.get("redirect")
                        or checkout.get("url")
                    )
                    if url:
                        return str(url)
                # Fallback: try to find any URL in response
                for key, value in (checkout or data or {}).items():
                    if isinstance(value, str) and value.startswith("http"):
                        return value
                raise RuntimeError("BePaid response did not contain redirect URL")

    async def create_card_payment_byn(self, user_id: int, tokens: int, price_byn: int) -> str:
        if not self._bepaid_auth:
            raise RuntimeError("BePaid credentials are not configured")

        payload: dict[str, Any] = {
            "checkout": {
                "transaction_type": "payment",
                "order": {
                    "amount": int(price_byn) * 100,
                    "currency": "BYN",
                    "description": f"Vento tokens: {tokens} for user {user_id}",
                    "tracking_id": f"{user_id}:{tokens}",
                },
                "customer": {
                    "first_name": str(user_id),
                },
                "settings": {
                    "notification_url": f"{settings.WEBHOOKS.BASE_URL}/webhooks/bepaid",
                    "success_url": "https://t.me/vento_toolbot",
                    "decline_url": "https://t.me/vento_toolbot",
                    "fail_url": "https://t.me/vento_toolbot",
                    "cancel_url": "https://t.me/vento_toolbot",
                    "language": "ru",
                },
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Version": "2",
            "Authorization": f"Basic {self._bepaid_auth}",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://checkout.bepaid.by/ctp/api/checkouts",
                data=json.dumps(payload),
                headers=headers,
            ) as resp:
                data = await resp.json(content_type=None)
                if resp.status not in {200, 201}:
                    raise RuntimeError(f"BePaid error {resp.status}: {data}")
                checkout = data.get("checkout") if isinstance(data, dict) else None
                if isinstance(checkout, dict):
                    url = (
                        checkout.get("redirect_url")
                        or checkout.get("redirect_to")
                        or checkout.get("redirect")
                        or checkout.get("url")
                    )
                    if url:
                        return str(url)
                for key, value in (checkout or data or {}).items():
                    if isinstance(value, str) and value.startswith("http"):
                        return value
                raise RuntimeError("BePaid response did not contain redirect URL")

    async def create_ru_subscription(self, user_id: int, price_rub: int) -> str:
        if not (settings.YOOKASSA.SHOP_ID and settings.YOOKASSA.SECRET_KEY):
            raise RuntimeError("YooKassa credentials are not configured")

        # Use metadata to mark subscription purchase
        payment = Payment.create({
            "amount": {"value": f"{price_rub}.00", "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": "https://t.me"},
            "capture": True,
            "description": f"Vento subscription: gpt_30 for user {user_id}",
            "metadata": {"user_id": user_id, "subscription": "gpt_30", "bonus_tokens": 2000},
        })
        return payment.confirmation.confirmation_url

    async def create_card_subscription(self, user_id: int, price_rub: int) -> str:
        if not self._bepaid_auth:
            raise RuntimeError("BePaid credentials are not configured")
        payload: dict[str, Any] = {
            "checkout": {
                "transaction_type": "payment",
                "order": {
                    "amount": int(price_rub) * 100,
                    "currency": "RUB",
                    "description": f"Vento subscription: gpt_30 for user {user_id}",
                    "tracking_id": f"{user_id}:sub",
                },
                "customer": {"first_name": str(user_id)},
                "settings": {
                    "notification_url": f"{settings.WEBHOOKS.BASE_URL}/webhooks/bepaid",
                    "success_url": "https://t.me/vento_toolbot",
                    "decline_url": "https://t.me/vento_toolbot",
                    "fail_url": "https://t.me/vento_toolbot",
                    "cancel_url": "https://t.me/vento_toolbot",
                    "language": "ru",
                },
            }
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Version": "2",
            "Authorization": f"Basic {self._bepaid_auth}",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://checkout.bepaid.by/ctp/api/checkouts", data=json.dumps(payload), headers=headers
            ) as resp:
                data = await resp.json(content_type=None)
                if resp.status not in {200, 201}:
                    raise RuntimeError(f"BePaid error {resp.status}: {data}")
                checkout = data.get("checkout") if isinstance(data, dict) else None
                if isinstance(checkout, dict):
                    url = (
                        checkout.get("redirect_url")
                        or checkout.get("redirect_to")
                        or checkout.get("redirect")
                        or checkout.get("url")
                    )
                    if url:
                        return str(url)
                for key, value in (checkout or data or {}).items():
                    if isinstance(value, str) and value.startswith("http"):
                        return value
                raise RuntimeError("BePaid response did not contain redirect URL")

    async def create_card_byn_subscription(self, user_id: int, price_byn: int) -> str:
        if not self._bepaid_auth:
            raise RuntimeError("BePaid credentials are not configured")
        payload: dict[str, Any] = {
            "checkout": {
                "transaction_type": "payment",
                "order": {
                    "amount": int(price_byn) * 100,
                    "currency": "BYN",
                    "description": f"Vento subscription: gpt_30 for user {user_id}",
                    "tracking_id": f"{user_id}:sub",
                },
                "customer": {"first_name": str(user_id)},
                "settings": {
                    "notification_url": f"{settings.WEBHOOKS.BASE_URL}/webhooks/bepaid",
                    "success_url": "https://t.me/vento_toolbot",
                    "decline_url": "https://t.me/vento_toolbot",
                    "fail_url": "https://t.me/vento_toolbot",
                    "cancel_url": "https://t.me/vento_toolbot",
                    "language": "ru",
                },
            }
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Version": "2",
            "Authorization": f"Basic {self._bepaid_auth}",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://checkout.bepaid.by/ctp/api/checkouts", data=json.dumps(payload), headers=headers
            ) as resp:
                data = await resp.json(content_type=None)
                if resp.status not in {200, 201}:
                    raise RuntimeError(f"BePaid error {resp.status}: {data}")
                checkout = data.get("checkout") if isinstance(data, dict) else None
                if isinstance(checkout, dict):
                    url = (
                        checkout.get("redirect_url")
                        or checkout.get("redirect_to")
                        or checkout.get("redirect")
                        or checkout.get("url")
                    )
                    if url:
                        return str(url)
                for key, value in (checkout or data or {}).items():
                    if isinstance(value, str) and value.startswith("http"):
                        return value
                raise RuntimeError("BePaid response did not contain redirect URL")

