import asyncio
import logging
import json
from aiohttp import web
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

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
from bot.container import Container
from bot.interfaces.uow import AbcUnitOfWork
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
    uow: AbcUnitOfWork = Provide[Container.uow],
) -> None:
    dp.include_router(router)

    app = web.Application()

    # Build a single sub-app for all webhooks
    webhooks_app = web.Application()
    admin_app = web.Application()

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
                # Invite user to continue or switch AI
                await bot.send_message(
                    user_id,
                    "🔄 Используй /start, чтобы выбрать другой ИИ или сгенерировать ещё один трек.",
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
    app.add_subapp('/admin', admin_app)

    # --- Admin API ---
    ADMIN_TOKEN = getattr(settings, 'ADMIN_TOKEN', None)

    def _ensure_admin(request: web.Request) -> bool:
        token = request.headers.get('X-Admin-Token') or request.query.get('token')
        return bool(ADMIN_TOKEN and token and token == ADMIN_TOKEN)

    def require_admin(handler):
        async def wrapper(request: web.Request):
            if not _ensure_admin(request):
                return web.json_response({"error": "forbidden"}, status=403)
            return await handler(request)
        return wrapper

    @require_admin
    async def stats_requests(request: web.Request):
        date = request.query.get('date')
        async with uow:
            if date:
                counts = await uow.ledger.requests_by_model_on_date(date)
            else:
                counts = await uow.ledger.requests_by_model_today()
        return web.json_response(counts.model_dump(by_alias=True))

    @require_admin
    async def user_stats(request: web.Request):
        user_id = int(request.query.get('user_id', '0') or 0)
        username = request.query.get('username')
        telegram_id = int(request.query.get('telegram_id', '0') or 0)
        async with uow:
            user = None
            if user_id:
                user = await uow.user.get_by_id(user_id)
            elif telegram_id:
                user = await uow.user.get_by_telegram_id(telegram_id)
            elif username:
                user = await uow.user.get_by_username(username)
            if not user:
                return web.json_response({"error": "user not found"}, status=404)
            totals = await uow.ledger.user_totals(user.id)
        data = totals.model_dump(by_alias=True)
        data.update({
            "user": {
                "id": user.id if user else None,
                "telegram_id": user.telegram_id if user else None,
                "username": user.username if user else None,
                "created_at": user.created_at.isoformat() if user and user.created_at else None,
                "balance": user.balance if user else None,
            }
        })
        return web.json_response(data)

    @require_admin
    async def list_settings(request: web.Request):
        items = await settings_service.list_all()
        return web.json_response(items)

    @require_admin
    async def set_setting(request: web.Request):
        payload = await request.json()
        key = payload.get('key')
        value = payload.get('value')
        if not key:
            return web.json_response({"error": "key required"}, status=400)
        await settings_service.set_value(str(key), str(value))
        return web.json_response({"ok": True})

    @require_admin
    async def block_user(request: web.Request):
        payload = await request.json()
        username = payload.get('username')
        telegram_id = payload.get('telegram_id')
        is_blocked = bool(payload.get('blocked', True))
        target_user = None
        async with uow:
            if username:
                updated = await uow.user.set_blocked_by_username(username, is_blocked)
                target_user = updated
            elif telegram_id:
                user = await uow.user.get_by_telegram_id(int(telegram_id))
                if not user:
                    return web.json_response({"error": "user not found"}, status=404)
                # emulate block by id via username update helper
                # direct update by username only exists; fallback to using repo update
                updated = await uow.user.update_balance_by_user_id(user.id, 0)  # no-op to load entity
                # direct SQL update for block flag
                await uow.session.execute(
                    "UPDATE \"user\" SET is_blocked = :blocked WHERE id = :id",
                    {"blocked": is_blocked, "id": user.id},
                )
                target_user = user
            else:
                return web.json_response({"error": "username or telegram_id required"}, status=400)
        return web.json_response({"ok": True, "blocked": is_blocked, "user": (target_user.username if target_user else None)})

    @require_admin
    async def admin_index(request: web.Request):
        html = (
            "<!doctype html><html><head><meta charset='utf-8'><title>Vento Admin</title>"
            "<style>body{font-family:system-ui,Arial;margin:20px;max-width:1100px}section{margin-bottom:28px}table{border-collapse:collapse}td,th{border:1px solid #ddd;padding:6px 10px}</style>"
            "</head><body>"
            "<h2>Vento Admin</h2>"
            "<section><h3>1) Статистика по моделям</h3>"
            "<label>Дата (YYYY-MM-DD, пусто = сегодня): <input id='date' /></label>"
            "<button onclick=loadStats()>Загрузить</button>"
            "<pre id='stats'></pre></section>"
            "<section><h3>2) Статистика по пользователю</h3>"
            "<label>telegram_id: <input id='tgid' /></label> или <label>username: <input id='uname' /></label>"
            "<button onclick=loadUser()>Загрузить</button>"
            "<pre id='user'></pre></section>"
            "<section><h3>3) Настройки</h3>"
            "<button onclick=loadSettings()>Показать</button>"
            "<div id='settings'></div>"
            "</section>"
            "<section><h3>4) Блокировка пользователя</h3>"
            "<label>telegram_id: <input id='blk_tgid' /></label> или <label>username: <input id='blk_uname' /></label>"
            "<select id='blk_flag'><option value='true'>заблокировать</option><option value='false'>разблокировать</option></select>"
            "<button onclick=blockUser()>Применить</button>"
            "<pre id='block_res'></pre>"
            "</section>"
            "<script>const token=new URLSearchParams(location.search).get('token')||prompt('Admin token?');"
            "async function loadStats(){const date=document.getElementById('date').value;const qs=new URLSearchParams({token, date});const r=await fetch('/admin/stats/requests?'+qs);document.getElementById('stats').textContent=JSON.stringify(await r.json(),null,2)}"
            "async function loadUser(){const tgid=document.getElementById('tgid').value;const uname=document.getElementById('uname').value;const qs=new URLSearchParams({token});if(tgid)qs.set('telegram_id',tgid);if(uname)qs.set('username',uname);const r=await fetch('/admin/users/stats?'+qs);document.getElementById('user').textContent=JSON.stringify(await r.json(),null,2)}"
            "async function loadSettings(){const r=await fetch('/admin/settings?token='+encodeURIComponent(token));const data=await r.json();const root=document.getElementById('settings');root.innerHTML='';for(const [k,v] of Object.entries(data)){const row=document.createElement('div');row.innerHTML=`<code>${k}</code> = <input data-k='${k}' value='${v}'/> <button>Save</button>`;row.querySelector('button').onclick=async()=>{const val=row.querySelector('input').value;await fetch('/admin/settings?token='+encodeURIComponent(token),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:k,value:val})});};root.appendChild(row);}}"
            "async function blockUser(){const tgid=document.getElementById('blk_tgid').value;const uname=document.getElementById('blk_uname').value;const blocked=document.getElementById('blk_flag').value==='true';const body={blocked};if(tgid)body.telegram_id=Number(tgid);if(uname)body.username=uname;const r=await fetch('/admin/users/block?token='+encodeURIComponent(token),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});document.getElementById('block_res').textContent=JSON.stringify(await r.json(),null,2)}"
            "</script>"
            "</body></html>"
        )
        return web.Response(text=html, content_type='text/html')

    admin_app.router.add_get('/', admin_index)
    admin_app.router.add_get('/stats/requests', stats_requests)
    admin_app.router.add_get('/users/stats', user_stats)
    admin_app.router.add_get('/settings', list_settings)
    admin_app.router.add_post('/settings', set_setting)
    admin_app.router.add_post('/users/block', block_user)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', settings.WEB_PORT)
    await site.start()

    # Scheduler: daily min balance top-up to 50
    scheduler = AsyncIOScheduler(timezone="UTC")

    async def _run_daily_topup():
        try:
            updated = await user_service.daily_min_balance_topup(50)
            logger.info("daily_topup_completed count=%s", updated)
        except Exception:
            logger.exception("daily_topup_failed")

    # Run daily at 03:00 UTC (adjust if needed)
    scheduler.add_job(_run_daily_topup, CronTrigger(hour=21, minute=0))
    scheduler.start()

    await dp.start_polling(bot)

async def main():
    async with lifecycle():
        await _run()

def start_bot():
    asyncio.run(main())
