import logging

from aiogram import Bot
from aiohttp import web

from bot.enums import BotModeEnum
from bot.interfaces.services.payments import AbcPaymentsService
from bot.interfaces.services.settings import AbcSettingsService
from bot.interfaces.services.user import AbcUserService
from bot.keyboards.start import start_keyboard

logger = logging.getLogger(__name__)


def create_app(
    payments: AbcPaymentsService,
    bot: Bot,
    user_service: AbcUserService,
    settings_service: AbcSettingsService,
) -> web.Application:
    app = web.Application()

    async def handle(request: web.Request):
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
                    try:
                        obj = body.get('object', {})
                        metadata = obj.get('metadata', {}) or {}
                        telegram_id = int(metadata.get('user_id')) if metadata.get('user_id') else None
                        tokens = int(metadata.get('tokens')) if metadata.get('tokens') else None
                        if telegram_id and tokens:
                            user = await user_service.get_user(telegram_id)
                            if user:
                                text = (
                                    f"✅ Оплата прошла успешно! Зачислено {tokens} токенов.\n\n"
                                    f"🪙 Твой баланс: *{user.balance}* токенов\n\n"
                                    "👇 Что хочешь сделать?"
                                )
                                await bot.send_message(telegram_id, text, reply_markup=start_keyboard(BotModeEnum.passive))
                    except Exception:
                        pass
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


