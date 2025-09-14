import logging
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

