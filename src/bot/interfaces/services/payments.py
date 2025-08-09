from abc import ABC, abstractmethod


class AbcPaymentsService(ABC):
    @abstractmethod
    async def create_invoice(self, telegram_id: int, amount_tokens: int) -> str:
        """Create payment invoice at lava.top and return pay URL."""
        ...

    @abstractmethod
    async def handle_webhook(self, payload: dict) -> None:
        """Handle payment webhook; should credit tokens on success."""
        ...


