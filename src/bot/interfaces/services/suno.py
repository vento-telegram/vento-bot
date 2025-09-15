from abc import ABC, abstractmethod

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.entities.user import UserEntity


class AbcSunoService(ABC):
    @abstractmethod
    async def submit_suno_request(
        self,
        message: Message,
        state: FSMContext,
        user: UserEntity,
        style: str,
        prompt: str,
        instrumental: bool,
    ) -> None:
        ...


