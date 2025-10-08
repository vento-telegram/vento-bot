import json
from aiohttp import web
from aiogram import Bot
import logging
from dependency_injector.wiring import inject, Provide

from bot.container import Container

logger = logging.getLogger(__name__)

@inject
async def nano_banana_handle(
    request: web.Request,
    bot: Bot = Provide[Container.bot],
):
    user_id = request.query.get("user_id")
    body = await request.json()

    code = body.get("code")
    data = body.get("data")

    state = data.get("state")
    result_json = data.get("resultJson")

    parsed = json.loads(result_json)
    result_urls = parsed.get("resultUrls")

    if not user_id:
        return web.json_response({"ok": False, "error": "no user_id"}, status=400)

    try:
        if code == 200 and state == "success" and result_urls:
            caption = "🏞️ Твоё изображение готово!\n\n✨ Cоздано с помощью [Vento](https://t.me/vento_toolbot)"
            await bot.send_photo(user_id, result_urls[0], caption=caption)
            for extra_url in result_urls[1:]:
                await bot.send_photo(user_id, extra_url, caption=caption)
        elif code == 200 and state in {"waiting"}:
            await bot.send_message(
                user_id, "🍌 Задача обрабатывается... Пришлю результат позже."
            )
        else:
            msg = data.get("failMsg") or body.get("msg") or "Генерация не удалась"
            await bot.send_message(user_id, f"☹️ {msg}")
    except Exception:
        logger.exception("Error sending KIE nano result to user %s", user_id)

    return web.json_response({"ok": True})