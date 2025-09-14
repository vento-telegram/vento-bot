import json
import logging
from aiohttp import web
from dependency_injector.wiring import Provide, inject

from bot.container import Container
from bot.interfaces.services.payments import AbcPaymentsService


logger = logging.getLogger(__name__)


def create_app() -> web.Application:
    app = web.Application()

    @inject
    async def handle(request: web.Request, payments: AbcPaymentsService = Provide[Container.payments_service]):
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"status": "bad json"}, status=400)

        event = body.get('event')
        if event == 'payment.succeeded':
            payment_id = body.get('object', {}).get('id')
            if payment_id:
                try:
                    credited = await payments.check_payment_and_credit(payment_id)
                    return web.json_response({"ok": credited})
                except Exception:
                    logger.exception("yookassa webhook error")
                    return web.json_response({"ok": False}, status=500)
        elif event == 'payment.canceled':
            logger.info('YooKassa payment.canceled: %s', body.get('object', {}).get('id'))
            return web.json_response({"ok": True})
        elif event == 'refund.succeeded':
            logger.info('YooKassa refund.succeeded: %s', body.get('object', {}).get('id'))
            return web.json_response({"ok": True})
        return web.json_response({"ok": True})

    app.router.add_post('/yookassa', handle)
    return app


