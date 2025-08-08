import asyncio
import logging

from aiogram import Bot, Dispatcher
from dependency_injector.wiring import Provide, inject

from bot.container import Container
from bot.container import lifecycle
from bot.enums import BotModeEnum
from bot.handlers import router

logging.basicConfig(level=logging.DEBUG)

@inject
async def _run(
    bot: Bot = Provide[Container.bot],
    dp: Dispatcher = Provide[Container.dispatcher],
) -> None:
    dp.include_router(router)
    await dp.start_polling(bot)

async def main():
    async with lifecycle():
        await _run()

def start_bot():
    asyncio.run(main())
