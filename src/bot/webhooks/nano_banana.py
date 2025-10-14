import json
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
async def nano_banana_handle(
    request: web.Request,
    bot: Bot = Provide[Container.bot],
    settings_service: AbcSettingsService = Provide[Container.settings_service],
    user_service: AbcUserService = Provide[Container.user_service],
):
    try:
        body = await request.json()
    except Exception:
        logger.exception("Nano Banana webhook: bad JSON body")
        return web.json_response({"ok": False, "error": "bad json"}, status=400)

    user_id = request.query.get("user_id")
    if not user_id:
        return web.json_response({"ok": False, "error": "no user_id"}, status=400)

    code = body.get("code")
    data = body.get("data") or {}

    state = data.get("state")
    result_json = data.get("resultJson")
    raw_error_message = (
        body.get("message")
        or data.get("message")
        or data.get("errorMessage")
        or data.get("error")
    )
    error_message = raw_error_message if isinstance(raw_error_message, str) else ""
    normalized_error_message = error_message.lower()

    result_urls = None
    try:
        if result_json:
            parsed = json.loads(result_json)
            result_urls = parsed.get("resultUrls")
    except Exception:
        logger.exception("Nano Banana webhook: failed to parse resultJson")

    support_text = (
        f"🚨 Произошла ошибка при взамодействии с моделью.\n\n"
        f"Свяжись с нашей поддержкой, чтобы получить помощь @{settings.SUPPORT_USERNAME}"
    )

    try:
        if code == 200 and state == "success" and result_urls:
            caption = "🏞️ Твоё изображение готово!\n\n✨ Cоздано с помощью [Vento](https://t.me/vento_toolbot)"
            await bot.send_photo(user_id, result_urls[0], caption=caption)
            for extra_url in result_urls[1:]:
                await bot.send_photo(user_id, extra_url, caption=caption)
        elif code == 200 and state in {"waiting"}:
            await bot.send_message(user_id, "Задача создаётся... Ещё немного.")
        else:
            logger.warning(
                "Nano Banana webhook: non-success or missing results: code=%s state=%s error=%r",
                code,
                state,
                raw_error_message,
            )
            if code == 422 or "no image content found in response" in normalized_error_message:
                if "flagged as sensitive" in normalized_error_message:
                    await bot.send_message(
                        user_id,
                        "🤐 Nano Banana отклонила запрос, потому что распознала чувствительное содержимое (цензура).\n\n"
                        "Пожалуйста, измените описание: избегайте запрещённых тем и используйте более нейтральные формулировки.",
                        parse_mode=None,
                    )
                elif "no image content found in response" in normalized_error_message:
                    await bot.send_message(
                        user_id,
                        "🤐 Nano Banana не поняла запрос и не смогла создать изображение.\n\n"
                        "Пожалуйста, измените формулировку: опишите сцену подробнее, уточните стиль или добавьте контекст.",
                        parse_mode=None,
                    )
            else:
                await bot.send_message(user_id, support_text, parse_mode=None)
            try:
                amount = int(await settings_service.get_value(settings_models_mapper[BotModeEnum.nano_banana]))
                await user_service.add_tokens_by_telegram_id(int(user_id), amount, TransactionReasonEnum.nano_banana_refund)
            except Exception:
                logger.exception("Failed to refund tokens for Nano Banana error user=%s", user_id)
    except Exception:
        logger.exception("Error sending Nano Banana result to user %s", user_id)
        try:
            await bot.send_message(user_id, support_text, parse_mode=None)
            try:
                amount = int(await settings_service.get_value(settings_models_mapper[BotModeEnum.nano_banana]))
                await user_service.add_tokens_by_telegram_id(int(user_id), amount, TransactionReasonEnum.nano_banana_refund)
            except Exception:
                logger.exception("Failed to refund tokens for Nano Banana error user=%s", user_id)
        except Exception:
            pass

    return web.json_response({"ok": True})
