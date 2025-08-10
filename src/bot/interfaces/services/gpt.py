from abc import ABC, abstractmethod

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.schemas import GPTMessageResponse
from openai.types.chat import ChatCompletionMessageParam


class AbcOpenAIService(ABC):
    @abstractmethod
    async def process_gpt_request(self, message: Message, state: FSMContext) -> GPTMessageResponse:
        ...

    @abstractmethod
    async def process_dalle_request(self, message: Message, history: list[ChatCompletionMessageParam] | None = None) -> GPTMessageResponse:
        ...