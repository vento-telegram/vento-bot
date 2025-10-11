import logging

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiohttp import web
from aiogram import Bot, Dispatcher
from dependency_injector.wiring import inject, Provide

from bot.container import Container
from bot.enums import BotModeEnum
from bot.settings import settings

logger = logging.getLogger(__name__)


@inject
async def suno_handle(
    request: web.Request,
    bot: Bot = Provide[Container.bot],
    dp: Dispatcher = Provide[Container.dispatcher],
):
    try:
        body = await request.json()
    except Exception:
        logger.exception("Suno webhook: bad JSON body")
        return web.json_response({"ok": False, "error": "bad json"}, status=400)

    user_id = request.query.get("user_id")
    if not user_id:
        return web.json_response({"ok": False, "error": "no user_id"}, status=400)

    code = body.get("code")
    data = body.get("data") or {}

    callback_type = data.get("callbackType")
    tracks = data.get("data")

    support_text = (
        f"🚨 Произошла ошибка при взамодействии с моделью.\n\n"
        f"Свяжись с нашей поддержкой, чтобы получить помощь @{settings.SUPPORT_USERNAME}"
    )

    try:
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
                "✅ Вернись /start, чтобы выбрать новый режим и задать новую задачу.",
            )
        elif code == 200:
            # ignore interim callbacks
            pass
        else:
            logger.warning(
                "Suno webhook: non-success or missing tracks: code=%s type=%s",
                code,
                callback_type,
            )
            await bot.send_message(user_id, support_text)
    except Exception:
        logger.exception("Error sending Suno result to user %s", user_id)
        try:
            await bot.send_message(user_id, support_text)
        except Exception:
            pass

    return web.json_response({"ok": True})

