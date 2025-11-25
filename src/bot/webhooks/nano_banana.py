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

    logger.info(f"Nano Banana webhook: {body}")

    user_id_raw = request.query.get("user_id")
    if not user_id_raw:
        return web.json_response({"ok": False, "error": "no user_id"}, status=400)
    try:
        chat_id = int(user_id_raw)
    except (TypeError, ValueError):
        return web.json_response({"ok": False, "error": "bad user_id"}, status=400)
    
    # Determine which model type this callback is for
    model_type = request.query.get("model", "nano_banana")  # default to nano_banana for backward compat
    is_pro = model_type == "nano_banana_pro"
    model_name = "Nano Banana Pro" if is_pro else "Nano Banana"
    logger.info(f"Webhook for model: {model_name} (type={model_type})")

    code = body.get("code")
    data = body.get("data") or {}
    fail_code = data.get("failCode")

    state = data.get("state")
    result_json = data.get("resultJson")
    raw_error_message = data.get("failMsg")
    error_message = raw_error_message if isinstance(raw_error_message, str) else ""
    normalized_error_message = error_message.lower()

    # Log the entire data structure for debugging
    logger.info(f"Webhook full data structure: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    result_urls = None
    try:
        if result_json:
            parsed = json.loads(result_json)
            result_urls = parsed.get("resultUrls")
            logger.info(f"Parsed resultJson: {parsed}, result_urls: {result_urls}")
        # Try alternative path: data.resultUrls directly
        elif "resultUrls" in data:
            result_urls = data.get("resultUrls")
            logger.info(f"Found resultUrls directly in data: {result_urls}")
    except Exception:
        logger.exception("Nano Banana webhook: failed to parse resultJson")
    
    logger.info(f"Webhook parsed - code: {code}, state: {state}, result_urls: {result_urls}, fail_code: {fail_code}")

    support_text = (
        f"🚨 Произошла ошибка при взамодействии с моделью.\n\n"
        f"Свяжись с нашей поддержкой, чтобы получить помощь @{settings.SUPPORT_USERNAME}"
    )

    try:
        # Check for success: code 200, state is success/completed/succeeded, and we have result URLs
        is_success = (
            code == 200 
            and state in {"success", "completed", "succeeded"} 
            and result_urls 
            and len(result_urls) > 0
        )
        
        logger.info(f"Success check: code={code}, state={state}, result_urls={result_urls}, is_success={is_success}")
        
        if is_success:
            caption = "🏞️ Твоё изображение готово!\n\n✨ Cоздано с помощью [Vento](https://t.me/vento_toolbot)"
            await bot.send_photo(chat_id, result_urls[0], caption=caption)
            for extra_url in result_urls[1:]:
                await bot.send_photo(chat_id, extra_url, caption=caption)
        elif code == 200 and state in {"waiting", "processing", "pending"}:
            await bot.send_message(chat_id, "Задача создаётся... Ещё немного.")
        else:
            logger.warning(
                "Nano Banana webhook: non-success or missing results: code=%s fail_code=%s state=%s error=%r",
                code,
                fail_code,
                state,
                raw_error_message,
            )
            handled_error = False
            logger.info(normalized_error_message)
            if "flagged as sensitive" in normalized_error_message:
                await bot.send_message(
                    chat_id,
                    "🤐 Nano Banana Pro отклонила запрос, потому что распознала чувствительное содержимое (цензура).\n\n"
                    "Пожалуйста, измените описание: избегайте запрещённых тем и используйте более нейтральные формулировки.",
                    parse_mode=None,
                )
                handled_error = True
            elif "no image content found in response" in normalized_error_message:
                await bot.send_message(
                    chat_id,
                    "🤐 Nano Banana Pro не поняла запрос и не смогла создать изображение.\n\n"
                    "Пожалуйста, измените формулировку: опишите сцену подробнее, уточните стиль или добавьте контекст.",
                    parse_mode=None,
                )
                handled_error = True
            elif fail_code == '422':
                await bot.send_message(chat_id, support_text, parse_mode=None)
                handled_error = True
            if not handled_error:
                await bot.send_message(chat_id, support_text, parse_mode=None)
            try:
                mode = BotModeEnum.nano_banana_pro if is_pro else BotModeEnum.nano_banana
                refund_reason = TransactionReasonEnum.nano_banana_pro_refund if is_pro else TransactionReasonEnum.nano_banana_refund
                amount = int(await settings_service.get_value(settings_models_mapper[mode]))
                await user_service.add_tokens_by_telegram_id(chat_id, amount, refund_reason)
            except Exception:
                logger.exception("Failed to refund tokens for Nano Banana error user=%s", chat_id)
    except Exception:
        logger.exception("Error sending Nano Banana result to user %s", chat_id)
        try:
            await bot.send_message(chat_id, support_text, parse_mode=None)
            try:
                mode = BotModeEnum.nano_banana_pro if is_pro else BotModeEnum.nano_banana
                refund_reason = TransactionReasonEnum.nano_banana_pro_refund if is_pro else TransactionReasonEnum.nano_banana_refund
                amount = int(await settings_service.get_value(settings_models_mapper[mode]))
                await user_service.add_tokens_by_telegram_id(chat_id, amount, refund_reason)
            except Exception:
                logger.exception("Failed to refund tokens for Nano Banana error user=%s", chat_id)
        except Exception:
            pass

    return web.json_response({"ok": True})
