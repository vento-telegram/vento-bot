from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dependency_injector import containers, providers
from openai import AsyncOpenAI

from bot.database.connection import AlchemyDatabase
from bot.database.uow import Uow
from bot.services.gpt import OpenAIService
from bot.services.user import UserService
from bot.settings import settings


from contextlib import asynccontextmanager
from typing import AsyncIterator


class Container(containers.DeclarativeContainer):
    db = providers.Singleton(AlchemyDatabase, settings=settings.POSTGRES)
    uow = providers.Factory(Uow, session_factory=db.provided.session_factory)
    bot = providers.Singleton(Bot, token=settings.MAIN_TOKEN)
    storage = providers.Singleton(MemoryStorage)
    dispatcher = providers.Singleton(Dispatcher, storage=storage)
    user_service = providers.Factory(UserService, uow=uow)
    openai_client = providers.Singleton(AsyncOpenAI, api_key=settings.OPENAI.API_KEY)
    openai_service = providers.Factory(OpenAIService, uow=uow, client=openai_client)


@asynccontextmanager
async def lifecycle() -> AsyncIterator[None]:
    _container = Container()
    _container.wire(modules=["bot.main"], packages=["bot"])
    try:
        yield
    finally:
        _container.unwire()
