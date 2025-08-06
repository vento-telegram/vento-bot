from abc import ABC, abstractmethod

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.schemas import GPTMessageResponse


class AbcOpenAIService(ABC):
    @abstractmethod
    async def process_message(self, message: Message, state: FSMContext) -> GPTMessageResponse:
        ...

    @abstractmethod
    async def generate_image(self, prompt: str) -> str:
        ...
