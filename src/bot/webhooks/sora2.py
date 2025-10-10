import json
import logging

from aiogram import Bot
from aiohttp import web
from dependency_injector.wiring import Provide, inject

from bot.container import Container

logger = logging.getLogger(__name__)


@inject
async def sora2_handle(
    request: web.Request,
    bot: Bot = Provide[Container.bot],
):
    user_id = request.query.get("user_id")
    body = await request.json()

    code = body.get("code")
    data = body.get("data") or {}

    state = data.get("state")
    result_json = data.get("resultJson")

    result_urls: list[str] | None = None
    try:
        if result_json:
            parsed = json.loads(result_json)
            result_urls = parsed.get("resultUrls")
    except Exception:
        logger.exception("Failed to parse Sora2 resultJson")

    if not user_id:
        return web.json_response({"ok": False, "error": "no user_id"}, status=400)

    try:
        if code == 200 and state == "success" and result_urls:
            caption = "🎉 Готово!\n\nCделано в [Vento](https://t.me/vento_toolbot)"
            try:
                await bot.send_video(user_id, result_urls[0], caption=caption)
            except Exception:
                await bot.send_message(user_id, f"Видео: {result_urls[0]}")
            for extra_url in (result_urls[1:] or []):
                try:
                    await bot.send_video(user_id, extra_url, caption=caption)
                except Exception:
                    await bot.send_message(user_id, f"Видео: {extra_url}")
        elif code == 200 and state in {"waiting"}:
            await bot.send_message(user_id, "Задача Sora 2 выполняется... Я пришлю результат, когда будет готово.")
        else:
            msg = data.get("failMsg") or body.get("msg") or "Не удалось получить результат"
            await bot.send_message(user_id, f"Упс, ошибка: {msg}")
    except Exception:
        logger.exception("Error sending Sora2 webhook result to user %s", user_id)

    return web.json_response({"ok": True})

