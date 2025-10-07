import asyncio
import logging

from aiogram import Bot, Dispatcher
from dependency_injector.wiring import Provide, inject

from bot.cronjobs import init_jobs_scheduler
from bot.webhooks import init_api_webhooks
from bot.container import Container, lifecycle
from bot.handlers import handlers_router

logging.basicConfig(level=logging.DEBUG)


@inject
async def _run(bot: Bot = Provide[Container.bot], dispatcher: Dispatcher = Provide[Container.dispatcher]) -> None:
    await init_api_webhooks()
    await init_jobs_scheduler()

    dispatcher.include_router(handlers_router)
    await dispatcher.start_polling(bot)


async def main() -> None:
    async with lifecycle():
        await _run()


def start_bot() -> None:
    asyncio.run(main())
