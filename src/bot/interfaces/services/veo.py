from abc import ABC, abstractmethod

from aiogram.types import Message

from bot.schemas import GPTMessageResponse


class AbcVeoService(ABC):
    @abstractmethod
    async def process_request(self, message: Message, aspect_ratio: str | None = None) -> GPTMessageResponse:
        ...


