from abc import ABC, abstractmethod

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.entities.user import UserEntity
from bot.schemas import GPTMessageResponse


class AbcOpenAIService(ABC):
    @abstractmethod
    async def process_gpt_request(
        self,
        message: Message,
        state: FSMContext,
        user: UserEntity
    ) -> GPTMessageResponse:
        ...

    @abstractmethod
    async def submit_nano_banana_request(
        self,
        message: Message,
        state: FSMContext,
        user: UserEntity,
        image_size: str,
    ) -> None:
        ...

    @abstractmethod
    async def submit_nano_banana_pro_request(
        self,
        message: Message,
        state: FSMContext,
        user: UserEntity,
        image_size: str,
    ) -> None:
        ...