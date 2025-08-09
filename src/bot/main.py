import asyncio
import base64
import hmac
import logging

from aiogram import Bot, Dispatcher
from aiohttp import web
from dependency_injector.wiring import Provide, inject

from bot.container import Container
from bot.container import lifecycle
from bot.handlers import router
from bot.interfaces.services.payments import AbcPaymentsService
from bot.settings import settings

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

def _safe_eq(a: str, b: str) -> bool:
    a = a or ""
    b = b or ""
    try:
        return hmac.compare_digest(a, b)
    except Exception:
        return False

def _check_api_key(request: web.Request, api_key: str) -> bool:
    if _safe_eq(request.headers.get("X-Api-Key"), api_key):
        return True
    return False

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
        logger.info(f"Webhook received for {request.method} {request.path}. Headers: {request.headers}. Payload: {await request.text()}")
        ok = _check_api_key(request, settings.PAYMENTS_WEBHOOK_API_KEY)
        if not ok:
            return web.Response(status=401, text="Unauthorized")

        # ---- payload ----
        try:
            payload = await request.json()
        except Exception:
            return web.Response(status=400, text="Bad JSON")

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
