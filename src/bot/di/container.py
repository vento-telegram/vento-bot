from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dependency_injector import containers, providers

from bot.database.connection import AlchemyDatabase
from bot.database.uow import Uow
from bot.settings import settings


class Container(containers.DeclarativeContainer):
    db = providers.Singleton(AlchemyDatabase, settings=settings.POSTGRES)
    uow = providers.Factory(Uow, session_factory=db.provided.session_factory)
    bot = providers.Singleton(Bot, token=settings.MAIN_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = providers.Singleton(Dispatcher)
    user_service = providers.Factory(
        UserService,
        uow=uow,
    )
