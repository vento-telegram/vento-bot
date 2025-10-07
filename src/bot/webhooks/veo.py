import json
import logging

from aiogram import Bot
from aiohttp import web
from dependency_injector.wiring import inject, Provide

from bot.container import Container

logger = logging.getLogger(__name__)

@inject
async def veo_handle(
    request: web.Request,
    bot: Bot = Provide[Container.bot],
):
    user_id = request.query.get("user_id")
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"status": "bad json"}, status=400)

    code = body.get("code")
    data = body.get("data") or {}
    info = data.get("info") or {}
    # In callbacks, resultUrls is JSON array or direct array depending on docs; try both
    result_urls: list[str] = []
    try:
        ru = info.get("resultUrls")
        if isinstance(ru, str):
            result_urls = json.loads(ru)
        elif isinstance(ru, list):
            result_urls = ru
    except Exception:
        result_urls = []

    if not user_id:
        return web.json_response({"ok": False, "error": "no user_id"}, status=400)

    try:
        if code == 200 and result_urls:
            caption = "🎬 Вот твоё видео!\n\n✨ Cоздано с помощью [Vento](https://t.me/vento_toolbot)"
            # Send first video as document/video; Telegram supports video by URL
            url0 = result_urls[0]
            try:
                await bot.send_video(user_id, url0, caption=caption)
            except Exception:
                await bot.send_message(user_id, f"Готово: {url0}")
            # Send extras as links to reduce spam
            for extra in result_urls[1:]:
                await bot.send_message(user_id, f"Доп. видео: {extra}")
        else:
            msg = body.get("msg") or "Генерация не удалась"
            await bot.send_message(user_id, f"☹️ {msg}")
    except Exception:
        logger.exception("Error sending Veo video to user %s", user_id)

    return web.json_response({"ok": True})