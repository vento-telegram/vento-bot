import asyncio
import logging
import json
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from dependency_injector.wiring import Provide, inject

from bot.container import Container
from bot.container import lifecycle
from bot.handlers import router
from bot.settings import settings
from bot.interfaces.services.payments import AbcPaymentsService
from bot.interfaces.services.user import AbcUserService
from bot.interfaces.services.settings import AbcSettingsService
from bot.enums import BotModeEnum
from bot.keyboards.start import start_keyboard

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

@inject
async def _run(
    bot: Bot = Provide[Container.bot],
    dp: Dispatcher = Provide[Container.dispatcher],
    payments: AbcPaymentsService = Provide[Container.payments_service],
    user_service: AbcUserService = Provide[Container.user_service],
    settings_service: AbcSettingsService = Provide[Container.settings_service],
) -> None:
    dp.include_router(router)

    app = web.Application()

    # Build a single sub-app for all webhooks
    webhooks_app = web.Application()

    async def yookassa_handle(request: web.Request):
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"status": "bad json"}, status=400)

        event = body.get('event')
        if event == 'payment.succeeded':
            payment_id = body.get('object', {}).get('id')
            if payment_id:
                try:
                    credited = await payments.check_payment_and_credit(payment_id)
                    try:
                        obj = body.get('object', {})
                        metadata = obj.get('metadata', {}) or {}
                        telegram_id = int(metadata.get('user_id')) if metadata.get('user_id') else None
                        tokens = int(metadata.get('tokens')) if metadata.get('tokens') else None
                        if telegram_id and tokens:
                            user = await user_service.get_user(telegram_id)
                            if user:
                                text = (
                                    f"✅ Оплата прошла успешно! Зачислено {tokens} токенов.\n\n"
                                    f"🪙 Твой баланс: *{user.balance}* токенов\n\n"
                                    "👇 Что хочешь сделать?"
                                )
                                await bot.send_message(telegram_id, text, reply_markup=start_keyboard(BotModeEnum.passive))
                    except Exception:
                        pass
                    return web.json_response({"ok": credited})
                except Exception:
                    logger.exception("yookassa webhook error")
                    return web.json_response({"ok": False}, status=500)
        elif event == 'payment.canceled':
            logger.info('YooKassa payment.canceled: %s', body.get('object', {}).get('id'))
            return web.json_response({"ok": True})
        elif event == 'refund.succeeded':
            logger.info('YooKassa refund.succeeded: %s', body.get('object', {}).get('id'))
            return web.json_response({"ok": True})
        return web.json_response({"ok": True})

    async def kie_image_handle(request: web.Request):
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
                caption = "*Твоё изображение готово!*\n\n✨ Cоздано с помощью [Vento](https://t.me/vento_toolbot)"
                await bot.send_photo(user_id, result_urls[0], caption=caption)
                for extra_url in result_urls[1:]:
                    await bot.send_photo(user_id, extra_url, caption=caption)
            else:
                msg = body.get('msg') or 'Генерация не удалась'
                await bot.send_message(user_id, f"☹️ {msg}")
        except Exception:
            logger.exception("Error sending KIE image to user %s (task %s)", user_id, task_id)

        return web.json_response({"ok": True})

    async def veo_handle(request: web.Request):
        user_id = request.query.get('user_id')
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"status": "bad json"}, status=400)

        code = body.get('code')
        data = (body.get('data') or {})
        info = data.get('info') or {}
        # In callbacks, resultUrls is JSON array or direct array depending on docs; try both
        result_urls: list[str] = []
        try:
            ru = info.get('resultUrls')
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
                msg = body.get('msg') or 'Генерация не удалась'
                await bot.send_message(user_id, f"☹️ {msg}")
        except Exception:
            logger.exception("Error sending Veo video to user %s", user_id)

        return web.json_response({"ok": True})

    async def kie_nano_handle(request: web.Request):
        user_id = request.query.get('user_id')
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"status": "bad json"}, status=400)

        code = body.get('code')
        data = (body.get('data') or {})
        state = data.get('state')
        result_json = data.get('resultJson')
        result_urls: list[str] = []
        try:
            if result_json:
                parsed = json.loads(result_json)
                result_urls = parsed.get('resultUrls') or []
        except Exception:
            result_urls = []

        if not user_id:
            return web.json_response({"ok": False, "error": "no user_id"}, status=400)

        try:
            if code == 200 and state == 'success' and result_urls:
                caption = "Твоё изображение готово!\n\n✨ Cоздано с помощью [Vento](https://t.me/vento_toolbot)"
                await bot.send_photo(user_id, result_urls[0], caption=caption)
                for extra_url in result_urls[1:]:
                    await bot.send_photo(user_id, extra_url, caption=caption)
            elif code == 200 and state in {'waiting'}:
                await bot.send_message(user_id, "🍌 Задача обрабатывается... Пришлю результат позже.")
            else:
                msg = data.get('failMsg') or body.get('msg') or 'Генерация не удалась'
                await bot.send_message(user_id, f"☹️ {msg}")
        except Exception:
            logger.exception("Error sending KIE nano result to user %s", user_id)

        return web.json_response({"ok": True})

    async def suno_handle(request: web.Request):
        user_id = request.query.get('user_id')
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"status": "bad json"}, status=400)

        code = body.get('code')
        data = (body.get('data') or {})
        callback_type = data.get('callbackType')
        payload = data.get('data') or {}
        # Some docs show result under data.response.sunoData when polling; callbacks example shows data.data array
        tracks = []
        try:
            if isinstance(payload, list):
                tracks = payload
            elif isinstance(payload, dict):
                # fallback if payload is dict with sunoData
                tracks = payload.get('sunoData') or []
        except Exception:
            tracks = []

        if not user_id:
            return web.json_response({"ok": False, "error": "no user_id"}, status=400)

        try:
            if code == 200 and callback_type == "complete" and tracks:
                caption = "🎵 Твоя музыка готова!\n\n✨ Cоздано с помощью [Vento](https://t.me/vento_toolbot)"
                sent_any = False
                for t in tracks:
                    audio_url = t.get('audioUrl') or t.get('audio_url')
                    title = t.get('title') or '@vento_toolbot song'
                    if audio_url:
                        await bot.send_audio(user_id, audio_url, caption=caption, title=title)
                        sent_any = True
                if not sent_any:
                    await bot.send_message(user_id, "☹️ Не удалось получить ссылку на аудио.")
                # Reset Suno flow state so next message expects a new style
                try:
                    key = StorageKey(bot_id=bot.id, chat_id=int(user_id), user_id=int(user_id))
                    fsm = FSMContext(storage=dp.storage, key=key)
                    await fsm.update_data(suno_style=None, suno_style_pending=True, suno_instrumental=None, suno_custom_mode=None)
                except Exception:
                    pass
                # Invite user to start a new Suno flow or switch AI
                await bot.send_message(
                    user_id,
                    (
                        "Хочешь ещё трек?\n\n"
                        "🧑‍🎤 Напиши стиль (жанры/описание), например: 'Быстрый эпичный рок'.\n\n"
                        "Или используй /start, чтобы выбрать другой ИИ."
                    ),
                )
            elif code == 200:
                # Ignore non-complete stages
                pass
            else:
                msg = body.get('msg') or (data.get('errorMessage') if isinstance(data, dict) else None) or 'Генерация не удалась'
                await bot.send_message(user_id, f"☹️ {msg}")
        except Exception:
            logger.exception("Error sending Suno result to user %s", user_id)

        return web.json_response({"ok": True})

    webhooks_app.router.add_post('/yookassa', yookassa_handle)
    webhooks_app.router.add_post('/kie-image', kie_image_handle)
    webhooks_app.router.add_post('/kie-nano', kie_nano_handle)
    webhooks_app.router.add_post('/suno', suno_handle)
    webhooks_app.router.add_post('/veo', veo_handle)

    app.add_subapp('/webhooks', webhooks_app)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', settings.WEB_PORT)
    await site.start()

    await dp.start_polling(bot)

async def main():
    async with lifecycle():
        await _run()

def start_bot():
    asyncio.run(main())
