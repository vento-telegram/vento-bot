from abc import ABC, abstractmethod


class AbcPaymentsService(ABC):
    @abstractmethod
    async def create_ru_payment(self, user_id: int, tokens: int, price_rub: int) -> str:
        """Create payment and return confirmation URL."""
    @abstractmethod
    async def check_payment_and_credit(self, payment_id: str) -> bool:
        """Check payment and credit tokens if succeeded."""

    @abstractmethod
    async def create_card_payment(self, user_id: int, tokens: int, price_rub: int) -> str:
        """Create BePaid payment and return confirmation URL for card payment in RUB."""

    @abstractmethod
    async def create_card_payment_byn(self, user_id: int, tokens: int, price_byn: int) -> str:
        """Create BePaid payment and return confirmation URL for card payment in BYN."""
