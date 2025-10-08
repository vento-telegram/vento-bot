from aiogram import Bot
from aiohttp import web
import json
import logging

from dependency_injector.wiring import inject, Provide

from bot.container import Container
from bot.enums import TransactionReasonEnum, BotModeEnum
from bot.interfaces.services import AbcUserService
from bot.keyboards import start_keyboard

logger = logging.getLogger(__name__)

@inject
async def bepaid_handle(
    request: web.Request,
    bot: Bot = Provide[Container.bot],
    user_service: AbcUserService = Provide[Container.user_service],
):
    body = await request.json()

    logger.info(f"Bepaid Webhook triggered {json.dumps(body, ensure_ascii=False)}")

    transaction = body.get("transaction")
    status = transaction.get("status")  # "successful"
    tracking_id = transaction.get("tracking_id")  # "302893773:700"

    parts = tracking_id.split(":", maxsplit=1)
    telegram_id = int(parts[0])
    tokens = int(parts[1])

    if status != "successful":
        logger.info(f"Bepaid Webhook got not final status: {status} for tracking_id: {tracking_id}")
        return web.json_response({"ok": True})

    await user_service.add_tokens_by_telegram_id(
        telegram_id=telegram_id,
        amount=tokens,
        reason=TransactionReasonEnum.purchase_bepaid,
    )

    user = await user_service.get_user(telegram_id)
    await bot.send_message(
        telegram_id,
        text=(
            f"✅ Оплата прошла успешно! Зачислено {tokens} токенов.\n\n"
            f"🪙 Твой баланс: {f'*{user.balance}*'} токенов\n\n"
            "👇 Что хочешь сделать?"
        ),
        reply_markup=start_keyboard(BotModeEnum.passive),
    )

    return web.json_response({"ok": True})
