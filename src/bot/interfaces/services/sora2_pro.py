from abc import ABC, abstractmethod

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.entities.user import UserEntity


class AbcSora2ProService(ABC):
    @abstractmethod
    async def submit_sora2_pro_request(
        self,
        message: Message,
        state: FSMContext,
        user: UserEntity,
        prompt: str,
        image_urls: list[str] | None,
        aspect_ratio: str,
        n_frames: str,
    ) -> None:
        ...

