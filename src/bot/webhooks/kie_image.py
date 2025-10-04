import logging

from aiogram import Bot
from aiohttp import web

logger = logging.getLogger(__name__)


def create_app(bot: Bot) -> web.Application:
    app = web.Application()

    async def handle(request: web.Request):
        user_id = request.query.get('user_id')
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"status": "bad json"}, status=400)

        code = body.get('code')
        data = (body.get('data') or {})
        task_id = data.get('taskId')
        info = data.get('info') or {}
        result_urls = info.get('result_urls') or []

        if not user_id:
            return web.json_response({"ok": False, "error": "no user_id"}, status=400)

        try:
            if code == 200 and result_urls:
                caption = "✅ Изображение готово!"
                await bot.send_photo(user_id, result_urls[0], caption=caption)
                # If multiple, send as separate photos to avoid album complexity
                for extra_url in result_urls[1:]:
                    await bot.send_photo(user_id, extra_url)
            else:
                msg = body.get('msg') or 'Генерация не удалась'
                await bot.send_message(user_id, f"☹️ {msg}")
        except Exception:
            logger.exception("Error sending KIE image to user %s (task %s)", user_id, task_id)

        return web.json_response({"ok": True})

    app.router.add_post('/kie-image', handle)
    return app
