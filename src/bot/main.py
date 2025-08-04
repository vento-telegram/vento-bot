import asyncio
import logging

from aiogram import Bot, Dispatcher
from dependency_injector.wiring import Provide, inject

from bot.di.container import Container
from bot.di.lifecycle import container_lifecycle
from bot.handlers import common

logging.basicConfig(level=logging.DEBUG)

@inject
async def _run(
    bot: Bot = Provide[Container.bot],
    dp: Dispatcher = Provide[Container.dispatcher],
) -> None:
    dp.include_router(chat.router)
    await dp.start_polling(bot)

def start_bot():
    async def main():
        async with container_lifecycle():
            await _run()

    asyncio.run(main())
