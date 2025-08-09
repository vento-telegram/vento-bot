import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiohttp import web
from dependency_injector.wiring import Provide, inject

from bot.container import Container
from bot.container import lifecycle
from bot.handlers import router
from bot.interfaces.services.payments import AbcPaymentsService

logging.basicConfig(level=logging.DEBUG)

@inject
async def _run(
    bot: Bot = Provide[Container.bot],
    dp: Dispatcher = Provide[Container.dispatcher],
    payments: AbcPaymentsService = Provide[Container.payments_service],
) -> None:
    dp.include_router(router)

    # HTTP app for lava webhook
    app = web.Application()

    async def webhook(request: web.Request) -> web.Response:
        payload = await request.json()
        await payments.handle_webhook(payload)
        return web.Response(status=200, text="OK")

    app.add_routes([web.post("/lava/webhook", webhook)])

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    logging.info("Webhook HTTP server started on 0.0.0.0:8080")

    await dp.start_polling(bot)

async def main():
    async with lifecycle():
        await _run()

def start_bot():
    asyncio.run(main())
