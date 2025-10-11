import logging

from aiogram import Bot
from aiohttp import web
from dependency_injector.wiring import inject, Provide

from bot.container import Container
from bot.settings import settings

logger = logging.getLogger(__name__)


@inject
async def gpt_image_handle(
    request: web.Request,
    bot: Bot = Provide[Container.bot],
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
            await bot.send_message(user_id, support_text)
    except Exception:
        logger.exception(
            "Error sending KIE image to user %s (task %s)", user_id, task_id
        )
        try:
            await bot.send_message(user_id, support_text)
        except Exception:
            pass

    return web.json_response({"ok": True})

