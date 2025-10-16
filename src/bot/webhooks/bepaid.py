from aiogram import Bot
from aiogram.types import FSInputFile
from aiohttp import web
import json
import logging
from pathlib import Path

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
    tracking_id = transaction.get("tracking_id") or ""  # "302893773:3000"

    parts = tracking_id.split(":", maxsplit=1)
    try:
        telegram_id = int(parts[0])
        tokens = int(parts[1])
    except Exception:
        logger.exception("Invalid tracking_id in BePaid webhook: %s", tracking_id)
        return web.json_response({"ok": False, "error": "invalid tracking_id"}, status=400)

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

    if tokens == 7000:
        special_text = (
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
            special_text,
            reply_markup=start_keyboard(BotModeEnum.passive),
            parse_mode=None,
        )
        try:
            guide_path = (
                Path(__file__).resolve().parents[2] / "media" / "files" / "guide.pdf"
            )
            await bot.send_document(
                telegram_id,
                document=FSInputFile(guide_path.as_posix()),
            )
        except Exception:
            # Do not fail webhook if guide sending fails
            pass
    else:
        await bot.send_message(
            telegram_id,
            text=(
                f"🎉 Спасибо за покупку! Зачислено {tokens} токенов.\n\n"
                f"Ваш текущий баланс: *{getattr(user, 'balance', '—')}* токенов\n\n"
                "Хотите попробовать что-то новое?"
            ),
            reply_markup=start_keyboard(BotModeEnum.passive),
        )

    # Notify admins via admin bot
    try:
        admins = await user_service.list_admins()
        admin_text = (
            "Новая покупка (BePaid):\n"
            f"Пользователь: {telegram_id}"
            + (f" (@{getattr(user, 'username', None)})" if getattr(user, 'username', None) else "")
            + f"\nТокены: +{tokens}"
            + (f"\nБаланс: {getattr(user, 'balance', None)}" if getattr(user, 'balance', None) is not None else "")
        )
        for admin in admins:
            try:
                await admin_bot.send_message(admin.telegram_id, admin_text, parse_mode=None)
            except Exception:
                pass
    except Exception:
        pass

    return web.json_response({"ok": True})

