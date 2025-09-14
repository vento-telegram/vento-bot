import asyncio
import logging
from aiohttp import web

from aiogram import Bot, Dispatcher
from dependency_injector.wiring import Provide, inject

from bot.container import Container
from bot.container import lifecycle
from bot.handlers import router
from bot.settings import settings
from bot.webhooks.yookassa import create_app as create_yk_app
from bot.interfaces.services.payments import AbcPaymentsService

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

@inject
async def _run(
    bot: Bot = Provide[Container.bot],
    dp: Dispatcher = Provide[Container.dispatcher],
    payments: AbcPaymentsService = Provide[Container.payments_service],
) -> None:
    dp.include_router(router)

    app = web.Application()
    app.add_subapp('/webhooks', create_yk_app(payments))

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', settings.WEB_PORT)
    await site.start()

    await dp.start_polling(bot)

async def main():
    async with lifecycle():
        await _run()

def start_bot():
    asyncio.run(main())
