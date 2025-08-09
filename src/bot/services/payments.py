import json
import logging
from typing import Final

import httpx

from bot.enums import LedgerReasonEnum
from bot.interfaces.services.payments import AbcPaymentsService
from bot.interfaces.uow import AbcUnitOfWork
from bot.entities.ledger import LedgerEntity
from bot.settings import settings


logger = logging.getLogger(__name__)


_OFFER_BY_TOKENS: dict[int, str] = {
    1000: "a69b0010-7c27-4014-ab49-5aaf83e03dac",
    5500: "423bce7a-8f67-42aa-bb13-64540dad285b",
    12000: "e59c2ed6-b031-4320-9f90-bee50d6a1f87",
    32500: "cbaa6578-9b2c-40ae-91b8-c95491b1e2e8",
    70000: "c36bfcec-97ba-4732-9e8d-2e2cb9f0aceb",
}


class PaymentsService(AbcPaymentsService):
    _LAVA_API_URL: Final[str] = "https://gate.lava.top/api/v2"

    def __init__(self, uow: AbcUnitOfWork):
        self._uow = uow

    async def create_invoice(self, telegram_id: int, amount_tokens: int) -> str:
        offer_id = _OFFER_BY_TOKENS.get(amount_tokens)
        if not offer_id:
            raise ValueError("Unsupported tokens amount")

        email = f"{telegram_id}@mail.com"
        body = {
            "email": email,
            "offerId": offer_id,
            "currency": "RUB",
        }

        headers = {
            "X-Api-Key": settings.LAVA.API_KEY,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                f"{self._LAVA_API_URL}/invoice",
                headers=headers,
                content=json.dumps(body),
            )
            resp.raise_for_status()
            data = resp.json()
            pay_url = data.get("url") or data.get("payUrl") or data.get("paymentUrl")
            if not pay_url:
                logger.error("Unexpected invoice response: %s", data)
                raise RuntimeError("Failed to create invoice")
            return pay_url

    async def handle_webhook(self, payload: dict) -> None:
        event_type = payload.get("eventType")
        if event_type != "payment.success":
            return

        buyer = payload.get("buyer") or {}
        email = str(buyer.get("email") or "")
        if not email.endswith("@mail.com"):
            return
        tg_part = email.split("@", 1)[0]
        try:
            telegram_id = int(tg_part)
        except ValueError:
            logger.warning("Webhook email doesn't contain telegram id: %s", email)
            return

        tokens = None
        product = payload.get("product") or {}
        product_id = product.get("id")
        if product_id:
            for t, oid in _OFFER_BY_TOKENS.items():
                if oid == product_id:
                    tokens = t
                    break

        if tokens is None:
            rub = float(payload.get("amount") or 0)
            if 90 <= rub < 150:
                tokens = 1000
            elif 450 <= rub < 650:
                tokens = 5500
            elif 900 <= rub < 1500:
                tokens = 12000
            elif 2000 <= rub < 3000:
                tokens = 32500
            elif 4500 <= rub < 5500:
                tokens = 70000

        if not tokens:
            logger.error("Cannot determine tokens for webhook: %s", payload)
            return

        # Credit tokens
        async with self._uow:
            user = await self._uow.user.get_by_telegram_id(telegram_id)
            if not user:
                logger.error("User not found for telegram_id=%s", telegram_id)
                return
            updated = await self._uow.user.update_balance_by_user_id(user.id, tokens)
            if updated:
                await self._uow.ledger.add(
                    LedgerEntity(
                        user_id=user.id,
                        delta=tokens,
                        reason=LedgerReasonEnum.purchase_tokens,
                        meta=json.dumps({
                            "contractId": payload.get("contractId"),
                            "currency": payload.get("currency"),
                            "amount": payload.get("amount"),
                        }),
                    )
                )


