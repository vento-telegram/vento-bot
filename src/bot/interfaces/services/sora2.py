from abc import ABC, abstractmethod

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.entities.user import UserEntity


class AbcSora2Service(ABC):
    @abstractmethod
    async def submit_sora2_request(
        self,
        message: Message,
        state: FSMContext,
        user: UserEntity,
        prompt: str,
        image_urls: list[str] | None,
        aspect_ratio: str,
    ) -> None:
        ...

