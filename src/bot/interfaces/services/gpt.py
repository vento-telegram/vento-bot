from abc import ABC, abstractmethod

from aiogram.types import Message


class AbcOpenAIService(ABC):
    @abstractmethod
    async def process_message(self, message: Message) -> str:
        ...
