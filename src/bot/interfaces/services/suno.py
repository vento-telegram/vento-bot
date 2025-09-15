from abc import ABC, abstractmethod

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.entities.user import UserEntity


class AbcSunoService(ABC):
    @abstractmethod
    async def submit_generate_music(self, message: Message, state: FSMContext, user: UserEntity) -> None:
        ...

    @abstractmethod
    async def submit_extend_music(self, message: Message, state: FSMContext, user: UserEntity) -> None:
        ...

    @abstractmethod
    async def submit_add_instrumental(self, message: Message, state: FSMContext, user: UserEntity) -> None:
        ...

    @abstractmethod
    async def submit_add_vocals(self, message: Message, state: FSMContext, user: UserEntity) -> None:
        ...

    @abstractmethod
    async def submit_generate_lyrics(self, message: Message, state: FSMContext, user: UserEntity) -> None:
        ...

    @abstractmethod
    async def submit_vocal_separation(self, message: Message, state: FSMContext, user: UserEntity) -> None:
        ...

