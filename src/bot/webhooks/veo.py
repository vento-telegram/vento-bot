import json
import logging
from typing import Any

from aiogram import Bot
from aiohttp import web
from dependency_injector.wiring import Provide, inject

from bot.container import Container
from bot.enums import TransactionReasonEnum
from bot.interfaces.services.settings import AbcSettingsService
from bot.interfaces.services.user import AbcUserService
from bot.settings import settings

logger = logging.getLogger(__name__)

SUCCESS_STATES = {"success", "completed", "succeeded"}
PROCESSING_STATES = {"waiting", "processing", "pending", "running"}
SUCCESS_MESSAGE_HINTS = {
    "success",
    "video generated successfully",
    "completed successfully",
    "video generated",
}
URL_KEYS = {
    "resultUrl",
    "resultUrls",
    "videoUrl",
    "videoUrls",
    "originUrl",
    "originUrls",
    "url",
    "urls",
}


def _is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if not normalized:
            return False
        if normalized.isdigit():
            return normalized != "0"
        return normalized in {"true", "yes", "y", "on", "success"}
    return False


def _first_non_empty(*values: Any) -> str | None:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                continue
            return stripped
        return str(value)
    return None


def _extract_video_urls(data: dict[str, Any]) -> list[str]:
    urls: list[str] = []

    def _collect(value: Any) -> None:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                urls.append(stripped)
        elif isinstance(value, list):
            for item in value:
                _collect(item)
        elif isinstance(value, dict):
            for key, nested in value.items():
                if key in URL_KEYS:
                    _collect(nested)
                elif isinstance(nested, (dict, list)):
                    _collect(nested)

    result_json = data.get("resultJson")
    if isinstance(result_json, str) and result_json.strip():
        try:
            parsed = json.loads(result_json)
            _collect(parsed)
        except Exception:
            logger.exception("Veo webhook: failed to parse resultJson")

    response_payload = data.get("response")
    if isinstance(response_payload, str) and response_payload.strip():
        try:
            parsed_response = json.loads(response_payload)
            _collect(parsed_response)
        except Exception:
            logger.exception("Veo webhook: failed to parse response payload")

    _collect(data)

    # De-duplicate while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    return unique_urls


async def _refund_tokens(
    chat_id: int,
    quality: str,
    aspect_ratio: str,
    settings_service: AbcSettingsService,
    user_service: AbcUserService,
) -> None:
    try:
        charge_improved = (quality == "improved") or (aspect_ratio == "9:16")
        price_key = "veo_improved_price" if charge_improved else "veo_standard_price"
        amount_raw = await settings_service.get_value(price_key)
        amount = int(amount_raw or 0)
        if amount > 0:
            await user_service.add_tokens_by_telegram_id(chat_id, amount, TransactionReasonEnum.veo_refund)
    except Exception:
        logger.exception("Veo webhook: failed to refund tokens for user %s", chat_id)


@inject
async def veo_handle(
    request: web.Request,
    bot: Bot = Provide[Container.bot],
    settings_service: AbcSettingsService = Provide[Container.settings_service],
    user_service: AbcUserService = Provide[Container.user_service],
):
    try:
        body = await request.json()
    except Exception:
        logger.exception("Veo webhook: bad JSON body")
        return web.json_response({"ok": False, "error": "bad json"}, status=400)

    user_id_raw = request.query.get("user_id")
    if not user_id_raw:
        return web.json_response({"ok": False, "error": "no user_id"}, status=400)
    try:
        chat_id = int(user_id_raw)
    except (TypeError, ValueError):
        return web.json_response({"ok": False, "error": "bad user_id"}, status=400)

    quality = request.query.get("quality") or "standard"
    aspect_ratio = request.query.get("aspect") or "16:9"

    code = body.get("code")
    data = body.get("data") or {}
    state_raw = (data.get("state") or data.get("status") or "").strip()
    state = state_raw.lower()
    task_id = data.get("taskId") or data.get("task_id")
    video_urls = _extract_video_urls(data)
    success_flag = data.get("successFlag") or data.get("success_flag")
    success_flag_set = _is_truthy(success_flag)
    success_msg = False
    body_msg = (body.get("msg") or body.get("message") or "").strip()
    msg_error_candidate = None
    if body_msg:
        msg_lower = body_msg.lower()
        success_msg = any(hint in msg_lower for hint in SUCCESS_MESSAGE_HINTS)
        if not success_msg:
            msg_error_candidate = body_msg

    support_text = (
        "🚨 Произошла ошибка при взаимодействии с Veo3.\n\n"
        f"Свяжись с поддержкой @{settings.SUPPORT_USERNAME}, чтобы мы помогли."
    )

    try:
        success_condition = code == 200 and video_urls and (
            (state and state in SUCCESS_STATES) or success_flag_set or success_msg
        )
        processing_condition = code == 200 and (
            (state and state in PROCESSING_STATES) or (not state and not success_flag_set and not video_urls)
        )

        if success_condition:
            caption = "🎬 Твоё видео готово!\n\n✨ Создано с помощью [Vento](https://t.me/vento_toolbot)"
            for url in video_urls:
                try:
                    await bot.send_video(chat_id, url, caption=caption)
                except Exception:
                    await bot.send_message(chat_id, f"Ссылка на видео: {url}")
            logger.info(
                "Veo webhook success",
                extra={
                    "user_id": chat_id,
                    "task_id": task_id,
                    "state": state_raw,
                    "success_flag": success_flag,
                },
            )
        elif processing_condition:
            await bot.send_message(chat_id, "🎬 Veo3 ещё работает над роликом. Я пришлю ссылку, как только всё будет готово.")
        else:
            raw_error = _first_non_empty(
                data.get("failMsg"),
                data.get("failReason"),
                data.get("errorMessage"),
                body.get("error"),
                msg_error_candidate,
            ) or "неизвестная ошибка"
            await bot.send_message(
                chat_id,
                f"🤐 Veo3 не смог завершить задачу.\n\nОтвет сервиса: {raw_error}",
                parse_mode=None,
            )
            await _refund_tokens(chat_id, quality, aspect_ratio, settings_service, user_service)
            try:
                logger.warning(
                    "Veo webhook failure payload",
                    extra={
                        "body": body,
                        "query": dict(request.query),
                    },
                )
            except Exception:
                logger.warning("Veo webhook failure payload (fallback): %s", json.dumps(body, ensure_ascii=False))
            logger.warning(
                "Veo webhook failure",
                extra={
                    "user_id": chat_id,
                    "task_id": task_id,
                    "state": state_raw,
                    "success_flag": success_flag,
                    "video_urls_found": len(video_urls),
                    "error": raw_error,
                },
            )
    except Exception:
        logger.exception("Veo webhook: error delivering result to user %s", chat_id)
        try:
            await bot.send_message(chat_id, support_text, parse_mode=None)
        except Exception:
            pass

    return web.json_response({"ok": True})

