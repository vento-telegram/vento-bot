from aiogram import Bot
from aiohttp import web
import logging

from dependency_injector.wiring import inject, Provide

from bot.container import Container
from bot.enums import BotModeEnum
from bot.interfaces.services import AbcUserService
from bot.interfaces.services.payments import AbcPaymentsService
from bot.keyboards import start_keyboard

logger = logging.getLogger(__name__)

@inject
async def yookassa_handle(
    request: web.Request,
    bot: Bot = Provide[Container.bot],
    admin_bot: Bot = Provide[Container.admin_bot],
    user_service: AbcUserService = Provide[Container.user_service],
    payments: AbcPaymentsService = Provide[Container.payments_service],
):
    logger.info(f"JSON FOR DEBUGGING: \n\n\n{await request.json()}\n\n\n")
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"status": "bad json"}, status=400)

    event = body.get("event")
    if event == "payment.succeeded":
        payment_id = body.get("object", {}).get("id")
        if payment_id:
            try:
                credited = await payments.check_payment_and_credit(payment_id)
                try:
                    obj = body.get("object", {})
                    metadata = obj.get("metadata", {}) or {}
                    telegram_id = (
                        int(metadata.get("user_id"))
                        if metadata.get("user_id")
                        else None
                    )
                    tokens = (
                        int(metadata.get("tokens"))
                        if metadata.get("tokens")
                        else None
                    )
                    if telegram_id and tokens:
                        user = await user_service.get_user(telegram_id)
                        if user:
                            text = (
                                f"✅ Оплата прошла успешно! Зачислено {tokens} токенов.\n\n"
                                f"🪙 Твой баланс: *{user.balance}* токенов\n\n"
                                "👇 Что хочешь сделать?"
                            )
                            await bot.send_message(
                                telegram_id,
                                text,
                                reply_markup=start_keyboard(BotModeEnum.passive),
                            )
                            # Notify admins via admin bot
                            try:
                                admins = await user_service.list_admins()
                                admin_text = (
                                    "Успешная оплата (YooKassa):\n"
                                    f"Пользователь: {telegram_id}"
                                    + (f" (@{user.username})" if getattr(user, 'username', None) else "")
                                    + f"\nТокены: +{tokens}\nБаланс: {user.balance}"
                                )
                                for admin in admins:
                                    try:
                                        await admin_bot.send_message(admin.telegram_id, admin_text)
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                except Exception:
                    pass
                return web.json_response({"ok": credited})
            except Exception:
                logger.exception("yookassa webhook error")
                return web.json_response({"ok": False}, status=500)
    elif event == "payment.canceled":
        logger.info(
            "YooKassa payment.canceled: %s", body.get("object", {}).get("id")
        )
        return web.json_response({"ok": True})
    elif event == "refund.succeeded":
        logger.info(
            "YooKassa refund.succeeded: %s", body.get("object", {}).get("id")
        )
        return web.json_response({"ok": True})
    return web.json_response({"ok": True})
