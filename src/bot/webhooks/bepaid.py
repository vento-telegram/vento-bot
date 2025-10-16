from aiogram import Bot
from aiogram.types import FSInputFile
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
    admin_bot: Bot = Provide[Container.admin_bot],
    user_service: AbcUserService = Provide[Container.user_service],
):
    body = await request.json()

    logger.info(f"Bepaid Webhook triggered {json.dumps(body, ensure_ascii=False)}")

    transaction = body.get("transaction") or {}
    status = transaction.get("status")  # "successful"
    tracking_id = transaction.get("tracking_id")  # "302893773:7000"

    if not tracking_id:
        return web.json_response({"ok": True})

    parts = tracking_id.split(":", maxsplit=1)
    try:
        telegram_id = int(parts[0])
        tokens = int(parts[1])
    except Exception:
        logger.warning("Invalid tracking_id format: %s", tracking_id)
        return web.json_response({"ok": True})

    if status != "successful":
        logger.info(
            "Bepaid Webhook got not final status: %s for tracking_id: %s",
            status,
            tracking_id,
        )
        return web.json_response({"ok": True})

    await user_service.add_tokens_by_telegram_id(
        telegram_id=telegram_id,
        amount=tokens,
        reason=TransactionReasonEnum.purchase_bepaid,
    )

    user = await user_service.get_user(telegram_id)
    try:
        await bot.send_message(
            telegram_id,
            text=(
                f"✅ Оплата прошла успешно! Зачислено {tokens} токенов.\n\n"
                f"🪙 Твой баланс: {f'*{user.balance}*' if user else ''} токенов\n\n"
                "👇 Что хочешь сделать?"
            ),
            reply_markup=start_keyboard(BotModeEnum.passive),
        )
    except Exception:
        pass

    # Send guide for 7000-token bundle
    if tokens == 7000:
        try:
            special = (
                "🎉 Спасибо за покупку!\n\n"
                "Вы получили:\n"
                "🛸 7000 токенов — ваш личный запас для общения с ИИ\n"
                "🎁 Гайд по использованию — пошаговое руководство, как извлечь максимум из возможностей нашего бота.\n\n"
                "В гайде вы найдёте:\n"
                "✨ как правильно формулировать запросы,\n"
                "⚙️ примеры эффективных промтов,\n"
                "💡 способы ускорить и улучшить ответы ИИ,\n"
                "🚀 идеи для реальных задач — от работы до творчества.\n\n"
                "Приятного изучения и продуктивного общения с ИИ!"
            )
            await bot.send_message(
                telegram_id,
                special,
                reply_markup=start_keyboard(BotModeEnum.passive),
            )
            await bot.send_document(
                telegram_id,
                FSInputFile("src/media/files/guide.pdf"),
                caption="🎁 Гайд по использованию",
            )
        except Exception:
            pass

    # Notify admins via admin bot
    try:
        admins = await user_service.list_admins()
        username = f" (@{user.username})" if getattr(user, 'username', None) else ""
        admin_text = (
            "🫦 Успешная оплата (BePaid):\n"
            f"Покупатель: {telegram_id}{username}\n"
            f"Начислено: +{tokens}\n"
            f"Баланс: {user.balance if user else ''}"
        )
        for admin in admins:
            try:
                await admin_bot.send_message(admin.telegram_id, admin_text, parse_mode=None)
            except Exception:
                pass
    except Exception:
        pass

    return web.json_response({"ok": True})
