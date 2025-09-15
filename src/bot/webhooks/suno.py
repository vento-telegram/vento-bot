import logging
from aiohttp import web
from aiogram import Bot

logger = logging.getLogger(__name__)


def create_app(bot: Bot) -> web.Application:
    app = web.Application()

    async def _get_user_id(request: web.Request) -> int | None:
        try:
            user_id = request.query.get('user_id')
            return int(user_id) if user_id else None
        except Exception:
            return None

    async def _safe_json(request: web.Request) -> dict:
        try:
            return await request.json()
        except Exception:
            return {}

    async def _handle_tracks(user_id: int, payload: dict, header: str):
        try:
            data = (payload.get('data') or {})
            # Two possible schemas: {data: {callbackType, data: [...]}} or {data: {sunoData: [...]}}
            tracks = []
            if isinstance(data, dict):
                if 'data' in data and isinstance(data['data'], list):
                    tracks = data['data']
                elif 'sunoData' in data and isinstance(data['sunoData'], list):
                    tracks = data['sunoData']
            if not tracks:
                await bot.send_message(user_id, f"{header}: результаты пока недоступны.")
                return
            await bot.send_message(user_id, header)
            for t in tracks:
                audio_url = t.get('audio_url') or t.get('audioUrl')
                title = t.get('title') or 'Track'
                if audio_url:
                    try:
                        await bot.send_audio(user_id, audio_url, caption=title)
                    except Exception:
                        await bot.send_message(user_id, f"{title}: {audio_url}")
        except Exception:
            logger.exception("Error sending Suno tracks to user %s", user_id)

    async def suno_generate(request: web.Request):
        user_id = await _get_user_id(request)
        if not user_id:
            return web.json_response({"ok": False, "error": "no user_id"}, status=400)
        body = await _safe_json(request)
        code = body.get('code')
        if code == 200:
            await _handle_tracks(user_id, body, "🎵 Музыка готова!")
        else:
            await bot.send_message(user_id, f"☹️ Ошибка генерации музыки: {body.get('msg') or code}")
        return web.json_response({"ok": True})

    async def suno_extend(request: web.Request):
        user_id = await _get_user_id(request)
        if not user_id:
            return web.json_response({"ok": False, "error": "no user_id"}, status=400)
        body = await _safe_json(request)
        code = body.get('code')
        if code == 200:
            await _handle_tracks(user_id, body, "➕ Продление готово!")
        else:
            await bot.send_message(user_id, f"☹️ Ошибка продления: {body.get('msg') or code}")
        return web.json_response({"ok": True})

    async def suno_instrumental(request: web.Request):
        user_id = await _get_user_id(request)
        if not user_id:
            return web.json_response({"ok": False, "error": "no user_id"}, status=400)
        body = await _safe_json(request)
        code = body.get('code')
        if code == 200:
            await _handle_tracks(user_id, body, "🎶 Инструментал готов!")
        else:
            await bot.send_message(user_id, f"☹️ Ошибка инструментала: {body.get('msg') or code}")
        return web.json_response({"ok": True})

    async def suno_vocals(request: web.Request):
        user_id = await _get_user_id(request)
        if not user_id:
            return web.json_response({"ok": False, "error": "no user_id"}, status=400)
        body = await _safe_json(request)
        code = body.get('code')
        if code == 200:
            await _handle_tracks(user_id, body, "🎤 Вокал добавлен!")
        else:
            await bot.send_message(user_id, f"☹️ Ошибка вокала: {body.get('msg') or code}")
        return web.json_response({"ok": True})

    async def suno_lyrics(request: web.Request):
        user_id = await _get_user_id(request)
        if not user_id:
            return web.json_response({"ok": False, "error": "no user_id"}, status=400)
        body = await _safe_json(request)
        code = body.get('code')
        data = (body.get('data') or {})
        if code == 200:
            items = (data.get('data') or [])
            if items:
                for item in items:
                    title = item.get('title') or 'Lyrics'
                    text = item.get('text') or ''
                    await bot.send_message(user_id, f"📜 {title}\n\n{text}")
            else:
                await bot.send_message(user_id, "📜 Текст готов, но пустой результат")
        else:
            await bot.send_message(user_id, f"☹️ Ошибка генерации текста: {body.get('msg') or code}")
        return web.json_response({"ok": True})

    async def suno_vocal_separation(request: web.Request):
        user_id = await _get_user_id(request)
        if not user_id:
            return web.json_response({"ok": False, "error": "no user_id"}, status=400)
        body = await _safe_json(request)
        code = body.get('code')
        if code == 200:
            try:
                vinfo = (body.get('data') or {}).get('vocal_separation_info') or {}
                parts = []
                for key, label in [
                    ("instrumental_url", "Инструментал"),
                    ("vocal_url", "Вокал"),
                    ("backing_vocals_url", "Бэк‑вокал"),
                    ("drums_url", "Барабаны"),
                    ("bass_url", "Бас"),
                    ("guitar_url", "Гитара"),
                    ("keyboard_url", "Клавиши"),
                    ("percussion_url", "Перкуссия"),
                    ("strings_url", "Струнные"),
                    ("synth_url", "Синт"),
                    ("fx_url", "FX"),
                    ("brass_url", "Духовые"),
                    ("woodwinds_url", "Деревянные духовые"),
                ]:
                    url = vinfo.get(key)
                    if url:
                        parts.append((label, url))
                if not parts:
                    await bot.send_message(user_id, "🎚️ Разделение завершено, но файлов нет.")
                else:
                    await bot.send_message(user_id, "🎚️ Результаты разделения:")
                    for label, url in parts:
                        try:
                            await bot.send_audio(user_id, url, caption=label)
                        except Exception:
                            await bot.send_message(user_id, f"{label}: {url}")
            except Exception:
                logger.exception("Failed to send separation results")
        else:
            await bot.send_message(user_id, f"☹️ Ошибка разделения: {body.get('msg') or code}")
        return web.json_response({"ok": True})

    app.router.add_post('/suno-generate', suno_generate)
    app.router.add_post('/suno-extend', suno_extend)
    app.router.add_post('/suno-instrumental', suno_instrumental)
    app.router.add_post('/suno-vocals', suno_vocals)
    app.router.add_post('/suno-lyrics', suno_lyrics)
    app.router.add_post('/suno-vocal-separation', suno_vocal_separation)

    return app


