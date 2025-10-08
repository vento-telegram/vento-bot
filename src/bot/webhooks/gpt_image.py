import logging

from aiogram import Bot
from aiohttp import web
from dependency_injector.wiring import inject, Provide

from bot.container import Container

logger = logging.getLogger(__name__)


@inject
async def gpt_image_handle(
    request: web.Request,
    bot: Bot = Provide[Container.bot],
):
    body = await request.json()
    user_id = request.query.get("user_id")

    code = body.get("code")
    data = body.get("data")

    task_id = data.get("taskId")
    info = data.get("info")

    result_urls = info.get("result_urls")

    if not user_id:
        return web.json_response({"ok": False, "error": "no user_id"}, status=400)

    try:
        if code == 200 and result_urls:
            caption = "*🏞️ Твоё изображение готово!*\n\n✨ Cоздано с помощью [Vento](https://t.me/vento_toolbot)"
            await bot.send_photo(user_id, result_urls[0], caption=caption)
            for extra_url in result_urls[1:]:
                await bot.send_photo(user_id, extra_url, caption=caption)
        else:
            msg = body.get("msg") or "Генерация не удалась"
            await bot.send_message(user_id, f"☹️ {msg}")
    except Exception:
        logger.exception(
            "Error sending KIE image to user %s (task %s)", user_id, task_id
        )

    return web.json_response({"ok": True})