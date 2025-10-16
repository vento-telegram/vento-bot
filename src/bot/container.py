from contextlib import asynccontextmanager
from typing import AsyncIterator

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from dependency_injector import containers, providers
from openai import AsyncOpenAI
from redis.asyncio import Redis

from bot.database.connection import AlchemyDatabase
from bot.database.uow import Uow
from bot.services.gpt import OpenAIService
from bot.services.payments import PaymentsService
from bot.services.settings import SettingsService
from bot.services.suno import SunoService
from bot.services.user import UserService
from bot.services.veo import VeoService
from bot.services.sora2 import Sora2Service
from bot.services.subscription import SubscriptionService
from bot.settings import settings


class Container(containers.DeclarativeContainer):
    db = providers.Singleton(AlchemyDatabase, settings=settings.POSTGRES)
    uow = providers.Factory(Uow, session_factory=db.provided.session_factory)
    bot = providers.Singleton(
        Bot,
        token=settings.MAIN_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    admin_bot = providers.Singleton(
        Bot,
        token=settings.ADMIN_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    redis_client=providers.Singleton(
        Redis,
        host=settings.REDIS.HOST,
        port=settings.REDIS.PORT,
        password=settings.REDIS.PASSWORD,
        decode_responses=True
    )
    storage = providers.Singleton(
        RedisStorage,
        redis=redis_client,
        key_builder=DefaultKeyBuilder(with_bot_id=True)
    )
    dispatcher = providers.Singleton(Dispatcher, storage=storage)
    settings_service = providers.Factory(SettingsService, uow=uow)
    user_service = providers.Factory(UserService, uow=uow, settings_service=settings_service)
    subscription_service = providers.Factory(SubscriptionService, uow=uow, settings_service=settings_service)
    payments_service = providers.Factory(PaymentsService, uow=uow)
    openai_client = providers.Singleton(AsyncOpenAI, api_key=settings.OPENAI.API_KEY)
    openai_service = providers.Factory(OpenAIService, uow=uow, client=openai_client, settings_service=settings_service, subscription_service=subscription_service)
    suno_service = providers.Factory(SunoService, uow=uow, settings_service=settings_service)
    veo_service = providers.Factory(VeoService, uow=uow, settings_service=settings_service)
    sora2_service = providers.Factory(Sora2Service, uow=uow, settings_service=settings_service)


@asynccontextmanager
async def lifecycle() -> AsyncIterator[None]:
    _container = Container()
    _container.wire(packages=["bot"])
    try:
        yield
    finally:
        _container.unwire()
