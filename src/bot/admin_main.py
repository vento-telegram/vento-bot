import asyncio
import logging

from aiogram import Bot, Dispatcher
from dependency_injector.wiring import Provide, inject

from bot.container import Container, lifecycle
from bot.handlers.admin import router as admin_router  # register base admin handlers
import bot.handlers.admin_extra  # noqa: F401  # attach extra handlers onto the same router

logging.basicConfig(level=logging.DEBUG)


@inject
async def _run(
    admin_bot: Bot = Provide[Container.admin_bot],
    storage = Provide[Container.storage],
) -> None:
    dispatcher = Dispatcher(storage=storage)
    dispatcher.include_router(admin_router)
    await dispatcher.start_polling(admin_bot)


async def main() -> None:
    async with lifecycle():
        await _run()


def start_admin_bot() -> None:
    asyncio.run(main())
