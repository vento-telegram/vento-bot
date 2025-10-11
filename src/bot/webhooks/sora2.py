import json
import logging

from aiogram import Bot
from aiohttp import web
from dependency_injector.wiring import Provide, inject

from bot.container import Container
from bot.settings import settings
from bot.constants import settings_models_mapper
from bot.enums import BotModeEnum, TransactionReasonEnum
from bot.interfaces.services.settings import AbcSettingsService
from bot.interfaces.services.user import AbcUserService

logger = logging.getLogger(__name__)


@inject
async def sora2_handle(
    request: web.Request,
    bot: Bot = Provide[Container.bot],
    settings_service: AbcSettingsService = Provide[Container.settings_service],
    user_service: AbcUserService = Provide[Container.user_service],
):
    try:
        body = await request.json()
    except Exception:
        logger.exception("Sora2 webhook: bad JSON body")
        return web.json_response({"ok": False, "error": "bad json"}, status=400)

    user_id = request.query.get("user_id")
    if not user_id:
        return web.json_response({"ok": False, "error": "no user_id"}, status=400)

    code = body.get("code")
    data = body.get("data") or {}

    state = data.get("state")
    result_json = data.get("resultJson")

    result_urls = None
    try:
        if result_json:
            parsed = json.loads(result_json)
            result_urls = parsed.get("resultUrls")
    except Exception:
        logger.exception("Failed to parse Sora2 resultJson")

    support_text = (
        f"🚨 Произошла ошибка при взамодействии с моделью.\n\n"
        f"Свяжись с нашей поддержкой, чтобы получить помощь @{settings.SUPPORT_USERNAME}"
    )

    try:
        if code == 200 and state == "success" and result_urls:
            caption = "🎬 Твоё видео готово!\n\n✨ Создано с помощью [Vento](https://t.me/vento_toolbot)"
            try:
                await bot.send_video(user_id, result_urls[0], caption=caption)
            except Exception:
                await bot.send_message(user_id, f"Ссылка: {result_urls[0]}")
            for extra_url in (result_urls[1:] or []):
                try:
                    await bot.send_video(user_id, extra_url, caption=caption)
                except Exception:
                    await bot.send_message(user_id, f"Ссылка: {extra_url}")
        elif code == 200 and state in {"waiting"}:
            await bot.send_message(user_id, "Задача Sora 2 выполняется... Ещё немного и всё будет готово.")
        else:
            msg = (data.get("failMsg") or body.get("msg") or "").strip()
            if msg:
                logger.warning("Sora2 webhook reported error: %s", msg)
            low = msg.lower()
            if "photorealistic" in low and "people" in low:
                text = (
                    "🚫 Sora 2 не принимает изображения с фотореалистичными людьми.\n\n"
                    "Что можно сделать:\n"
                    "• убрать людей/лица с фото или размыть/замазать их;\n"
                    "• использовать рисунок/иллюстрацию вместо фотографии;\n"
                    "• отправить только текстовое описание без изображения.\n\n"
                    "После правки просто пришли запрос ещё раз."
                )
                await bot.send_message(user_id, text, parse_mode=None)
                try:
                    amount = int(await settings_service.get_value(settings_models_mapper[BotModeEnum.sora2_video]))
                    await user_service.add_tokens_by_telegram_id(int(user_id), amount, TransactionReasonEnum.sora2_refund)
                except Exception:
                    logger.exception("Failed to refund tokens for Sora2 photorealistic error user=%s", user_id)
            else:
                await bot.send_message(user_id, support_text, parse_mode=None)
                try:
                    amount = int(await settings_service.get_value(settings_models_mapper[BotModeEnum.sora2_video]))
                    await user_service.add_tokens_by_telegram_id(int(user_id), amount, TransactionReasonEnum.sora2_refund)
                except Exception:
                    logger.exception("Failed to refund tokens for Sora2 error user=%s", user_id)
    except Exception:
        logger.exception("Error sending Sora2 webhook result to user %s", user_id)
        try:
            await bot.send_message(user_id, support_text, parse_mode=None)
        except Exception:
            pass

    return web.json_response({"ok": True})
