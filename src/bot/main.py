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
from bot.interfaces.services.user import AbcUserService
from bot.interfaces.services.settings import AbcSettingsService

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

@inject
async def _run(
    bot: Bot = Provide[Container.bot],
    dp: Dispatcher = Provide[Container.dispatcher],
    payments: AbcPaymentsService = Provide[Container.payments_service],
    user_service: AbcUserService = Provide[Container.user_service],
    settings_service: AbcSettingsService = Provide[Container.settings_service],
) -> None:
    dp.include_router(router)

    app = web.Application()
    app.add_subapp('/webhooks', create_yk_app(payments, bot, user_service, settings_service))

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
