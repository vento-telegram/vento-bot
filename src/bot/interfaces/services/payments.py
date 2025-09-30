from abc import ABC, abstractmethod


class AbcPaymentsService(ABC):
    @abstractmethod
    async def create_ru_payment(self, user_id: int, tokens: int, price_rub: int) -> str:
        """Create payment and return confirmation URL."""
    @abstractmethod
    async def check_payment_and_credit(self, payment_id: str) -> bool:
        """Check payment and credit tokens if succeeded."""
