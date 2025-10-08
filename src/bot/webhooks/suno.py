from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiohttp import web
from aiogram import Bot, Dispatcher
import logging
from dependency_injector.wiring import inject, Provide

from bot.container import Container
from bot.enums import BotModeEnum

logger = logging.getLogger(__name__)


@inject
async def suno_handle(
    request: web.Request,
    bot: Bot = Provide[Container.bot],
    dp: Dispatcher = Provide[Container.dispatcher],
):
    user_id = request.query.get("user_id")

    body = await request.json()

    code = body.get("code")
    data = body.get("data")

    callback_type = data.get("callbackType")
    tracks = data.get("data")

    if not user_id:
        return web.json_response({"ok": False, "error": "no user_id"}, status=400)

    if code == 200 and callback_type == "complete" and tracks:
        caption = "🎵 Твоя музыка готова!\n\n✨ Cоздано с помощью [Vento](https://t.me/vento_toolbot)"
        for t in tracks:
            audio_url = t.get("audio_url")
            title = t.get("title")
            await bot.send_audio(
                user_id, audio_url, caption=caption, title=title
            )

        key = StorageKey(
            bot_id=bot.id, chat_id=int(user_id), user_id=int(user_id)
        )
        fsm = FSMContext(storage=dp.storage, key=key)
        await fsm.update_data(
            suno_style=None,
            suno_style_pending=False,
            suno_instrumental=None,
            suno_custom_mode=None,
            mode=BotModeEnum.passive,
        )

        await bot.send_message(
            user_id,
            "🔄 Используй /start, чтобы выбрать другой ИИ или сгенерировать ещё один трек.",
        )
    elif code == 200:
        pass
    else:
        msg = (
                body.get("msg")
                or (data.get("errorMessage") if isinstance(data, dict) else None)
                or "Генерация не удалась"
        )
        await bot.send_message(user_id, f"☹️ {msg}")

    return web.json_response({"ok": True})