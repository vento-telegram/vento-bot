from abc import ABC, abstractmethod


class AbcPaymentsService(ABC):
    @abstractmethod
    async def create_ru_payment(self, user_id: int, tokens: int, price_rub: int) -> str:
        """Create payment and return confirmation URL."""
    @abstractmethod
    async def check_payment_and_credit(self, payment_id: str) -> bool:
        """Check payment and credit tokens if succeeded."""
    @abstractmethod
    async def create_card_payment(self, user_id: int, tokens: int, amount_minor: int, currency: str) -> str:
        """Create bePaid card payment, return redirect_url for 3DS or receipt_url when successful."""
    @abstractmethod
    async def process_bepaid_webhook(self, payload: dict) -> tuple[bool, int | None, int | None]:
        """Process bePaid webhook; return tuple(success, telegram_id, tokens)."""
