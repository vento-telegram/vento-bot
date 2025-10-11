import logging

from aiogram import Bot
from aiohttp import web
from dependency_injector.wiring import inject, Provide

from bot.container import Container
from bot.settings import settings
from bot.constants import settings_models_mapper
from bot.enums import BotModeEnum, TransactionReasonEnum
from bot.interfaces.services.settings import AbcSettingsService
from bot.interfaces.services.user import AbcUserService

logger = logging.getLogger(__name__)


@inject
async def gpt_image_handle(
    request: web.Request,
    bot: Bot = Provide[Container.bot],
    settings_service: AbcSettingsService = Provide[Container.settings_service],
    user_service: AbcUserService = Provide[Container.user_service],
):
    try:
        body = await request.json()
    except Exception:
        logger.exception("KIE image webhook: bad JSON body")
        return web.json_response({"ok": False, "error": "bad json"}, status=400)

    user_id = request.query.get("user_id")
    if not user_id:
        return web.json_response({"ok": False, "error": "no user_id"}, status=400)

    code = body.get("code")
    data = body.get("data") or {}

    task_id = data.get("taskId")
    info = data.get("info") or {}
    result_urls = info.get("result_urls") if isinstance(info, dict) else None

    support_text = (
        f"🚨 Произошла ошибка при взамодействии с моделью.\n\n"
        f"Свяжись с нашей поддержкой, чтобы получить помощь @{settings.SUPPORT_USERNAME}"
    )

    try:
        if code == 200 and result_urls:
            caption = "*🏞️ Твоё изображение готово!*\n\n✨ Cоздано с помощью [Vento](https://t.me/vento_toolbot)"
            await bot.send_photo(user_id, result_urls[0], caption=caption)
            for extra_url in result_urls[1:]:
                await bot.send_photo(user_id, extra_url, caption=caption)
        else:
            logger.warning(
                "KIE image webhook: non-success or missing results: code=%s task=%s",
                code,
                task_id,
            )
            msg = (
                (body.get("msg") if isinstance(body, dict) else None)
                or (info.get("msg") if isinstance(info, dict) else None)
                or (info.get("error") if isinstance(info, dict) else None)
                or (info.get("message") if isinstance(info, dict) else None)
                or ""
            )
            low = (msg or "").strip().lower()
            if ("flagged" in low and "polic" in low) or ("violate" in low and "polic" in low):
                text = (
                    "🚫 Контент не прошёл проверку политики OpenAI.\n\n"
                    "Попробуй переформулировать запрос без тем: насилие, эротика/нагота, несовершеннолетние, опасные или незаконные действия, личные данные, дискриминация и т.п.\n\n"
                    "Сделай описание нейтральнее и отправь снова."
                )
                await bot.send_message(user_id, text, parse_mode=None)
            else:
                await bot.send_message(user_id, support_text, parse_mode=None)
            try:
                amount = int(await settings_service.get_value(settings_models_mapper[BotModeEnum.gpt_image]))
                await user_service.add_tokens_by_telegram_id(int(user_id), amount, TransactionReasonEnum.gpt_image_refund)
            except Exception:
                logger.exception("Failed to refund tokens for GPT Image error user=%s", user_id)
    except Exception:
        logger.exception(
            "Error sending KIE image to user %s (task %s)", user_id, task_id
        )
        try:
            await bot.send_message(user_id, support_text, parse_mode=None)
            try:
                amount = int(await settings_service.get_value(settings_models_mapper[BotModeEnum.gpt_image]))
                await user_service.add_tokens_by_telegram_id(int(user_id), amount, TransactionReasonEnum.gpt_image_refund)
            except Exception:
                logger.exception("Failed to refund tokens for GPT Image error user=%s", user_id)
        except Exception:
            pass

    return web.json_response({"ok": True})
