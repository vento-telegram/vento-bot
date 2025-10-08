from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiohttp import web
from aiogram import Bot, Dispatcher
import logging
from dependency_injector.wiring import inject, Provide

from bot.container import Container


logger = logging.getLogger(__name__)


@inject
async def suno_handle(
    request: web.Request,
    bot: Bot = Provide[Container.bot],
    dp: Dispatcher = Provide[Container.dispatcher],
):
    logger.info(f"JSON FOR DEBUGGING: \n\n\n{request.json()}\n\n\n")
    user_id = request.query.get("user_id")
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"status": "bad json"}, status=400)

    code = body.get("code")
    data = body.get("data") or {}
    callback_type = data.get("callbackType")
    payload = data.get("data") or {}
    # Some docs show result under data.response.sunoData when polling; callbacks example shows data.data array
    tracks = []
    try:
        if isinstance(payload, list):
            tracks = payload
        elif isinstance(payload, dict):
            # fallback if payload is dict with sunoData
            tracks = payload.get("sunoData") or []
    except Exception:
        tracks = []

    if not user_id:
        return web.json_response({"ok": False, "error": "no user_id"}, status=400)

    try:
        if code == 200 and callback_type == "complete" and tracks:
            caption = "🎵 Твоя музыка готова!\n\n✨ Cоздано с помощью [Vento](https://t.me/vento_toolbot)"
            sent_any = False
            for t in tracks:
                audio_url = t.get("audioUrl") or t.get("audio_url")
                title = t.get("title") or "@vento_toolbot song"
                if audio_url:
                    await bot.send_audio(
                        user_id, audio_url, caption=caption, title=title
                    )
                    sent_any = True
            if not sent_any:
                await bot.send_message(
                    user_id, "☹️ Не удалось получить ссылку на аудио."
                )
            # Reset Suno flow state so next message expects a new style
            try:
                key = StorageKey(
                    bot_id=bot.id, chat_id=int(user_id), user_id=int(user_id)
                )
                fsm = FSMContext(storage=dp.storage, key=key)
                await fsm.update_data(
                    suno_style=None,
                    suno_style_pending=True,
                    suno_instrumental=None,
                    suno_custom_mode=None,
                )
            except Exception:
                pass
            # Invite user to continue or switch AI
            await bot.send_message(
                user_id,
                "🔄 Используй /start, чтобы выбрать другой ИИ или сгенерировать ещё один трек.",
            )
        elif code == 200:
            # Ignore non-complete stages
            pass
        else:
            msg = (
                    body.get("msg")
                    or (data.get("errorMessage") if isinstance(data, dict) else None)
                    or "Генерация не удалась"
            )
            await bot.send_message(user_id, f"☹️ {msg}")
    except Exception:
        logger.exception("Error sending Suno result to user %s", user_id)

    return web.json_response({"ok": True})