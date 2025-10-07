import asyncio
import logging

from aiogram import Bot, Dispatcher
from dependency_injector.wiring import Provide, inject

from bot.cronjobs import init_jobs_scheduler
from bot.webhooks import init_api_webhooks
from bot.container import Container, lifecycle
from bot.handlers import router

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


@inject
async def _run(
    bot: Bot = Provide[Container.bot],
    dp: Dispatcher = Provide[Container.dispatcher],
) -> None:
    await init_api_webhooks()
    await init_jobs_scheduler()

    dp.include_router(router)
    await dp.start_polling(bot)


async def main():
    async with lifecycle():
        await _run()


def start_bot():
    asyncio.run(main())
