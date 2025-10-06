import asyncio
import json
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiohttp import web
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dependency_injector.wiring import Provide, inject

from bot.container import Container, lifecycle
from bot.enums import BotModeEnum, LedgerReasonEnum
from bot.handlers import router
from bot.interfaces.services.payments import AbcPaymentsService
from bot.interfaces.services.settings import AbcSettingsService
from bot.interfaces.services.user import AbcUserService
from bot.keyboards.start import start_keyboard
from bot.settings import settings

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


@inject
async def _run(
    bot: Bot = Provide[Container.bot],
    dp: Dispatcher = Provide[Container.dispatcher],
    payments: AbcPaymentsService = Provide[Container.payments_service],
    user_service: AbcUserService = Provide[Container.user_service],
) -> None:
    dp.include_router(router)

    app = web.Application()

    webhooks_app = web.Application()

    async def yookassa_handle(request: web.Request):
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"status": "bad json"}, status=400)

        event = body.get("event")
        if event == "payment.succeeded":
            payment_id = body.get("object", {}).get("id")
            if payment_id:
                try:
                    credited = await payments.check_payment_and_credit(payment_id)
                    try:
                        obj = body.get("object", {})
                        metadata = obj.get("metadata", {}) or {}
                        telegram_id = (
                            int(metadata.get("user_id"))
                            if metadata.get("user_id")
                            else None
                        )
                        tokens = (
                            int(metadata.get("tokens"))
                            if metadata.get("tokens")
                            else None
                        )
                        if telegram_id and tokens:
                            user = await user_service.get_user(telegram_id)
                            if user:
                                text = (
                                    f"✅ Оплата прошла успешно! Зачислено {tokens} токенов.\n\n"
                                    f"🪙 Твой баланс: *{user.balance}* токенов\n\n"
                                    "👇 Что хочешь сделать?"
                                )
                                await bot.send_message(
                                    telegram_id,
                                    text,
                                    reply_markup=start_keyboard(BotModeEnum.passive),
                                )
                    except Exception:
                        pass
                    return web.json_response({"ok": credited})
                except Exception:
                    logger.exception("yookassa webhook error")
                    return web.json_response({"ok": False}, status=500)
        elif event == "payment.canceled":
            logger.info(
                "YooKassa payment.canceled: %s", body.get("object", {}).get("id")
            )
            return web.json_response({"ok": True})
        elif event == "refund.succeeded":
            logger.info(
                "YooKassa refund.succeeded: %s", body.get("object", {}).get("id")
            )
            return web.json_response({"ok": True})
        return web.json_response({"ok": True})

    async def kie_image_handle(request: web.Request):
        user_id = request.query.get("user_id")
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"status": "bad json"}, status=400)

        code = body.get("code")
        data = body.get("data") or {}
        task_id = data.get("taskId")
        info = data.get("info") or {}
        result_urls = info.get("result_urls") or []

        if not user_id:
            return web.json_response({"ok": False, "error": "no user_id"}, status=400)

        try:
            if code == 200 and result_urls:
                caption = "*Твоё изображение готово!*\n\n✨ Cоздано с помощью [Vento](https://t.me/vento_toolbot)"
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

    async def bepaid_handle(request: web.Request):
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"status": "bad json"}, status=400)

        # Log payload for diagnostics (avoid secrets; BePaid doesn't include card data here)
        try:
            logger.info(
                "bepaid_webhook payload=%s", json.dumps(body, ensure_ascii=False)
            )
        except Exception:
            logger.info("bepaid_webhook payload=(non-json)")

        # BePaid sends notification with payment details; we expect tracking_id as "user_id:tokens"
        def _extract_status_and_tracking(
            payload: dict,
        ) -> tuple[str | None, str | None]:
            status_candidates: list[str | None] = []
            tracking_candidates: list[str | None] = []

            checkout = payload.get("checkout")
            if isinstance(checkout, dict):
                status_candidates.append(
                    checkout.get("status") or checkout.get("state")
                )
                order = checkout.get("order") or {}
                if isinstance(order, dict):
                    tracking_candidates.append(order.get("tracking_id"))

            transaction = payload.get("transaction")
            if isinstance(transaction, dict):
                status_candidates.append(transaction.get("status"))
                payment = transaction.get("payment") or {}
                if isinstance(payment, dict):
                    status_candidates.append(payment.get("status"))
                tracking_candidates.append(transaction.get("tracking_id"))
                order = transaction.get("order") or {}
                if isinstance(order, dict):
                    tracking_candidates.append(order.get("tracking_id"))

            status_candidates.append(payload.get("status"))
            tracking_candidates.append(payload.get("tracking_id"))

            status_val = next(
                (s for s in status_candidates if isinstance(s, str) and s), None
            )
            tracking_val = next(
                (t for t in tracking_candidates if isinstance(t, str) and t), None
            )
            return status_val, tracking_val

        status, tracking_id = _extract_status_and_tracking(body)
        telegram_id: int | None = None
        tokens: int | None = None
        try:
            parts = str(tracking_id or "").split(":", maxsplit=1)
            if parts and parts[0].isdigit():
                telegram_id = int(parts[0])
            if len(parts) >= 2 and parts[1].isdigit():
                tokens = int(parts[1])
        except Exception:
            telegram_id = None
            tokens = None

        if not (telegram_id and tokens and tokens > 0):
            logger.warning(
                "bepaid_webhook missing identifiers: status=%s tracking_id=%s",
                status,
                tracking_id,
            )
            return web.json_response({"ok": True})

        # Success statuses according to BePaid: often "successful"; allow a few variants
        status_norm = str(status or "").lower()
        success_statuses = {"successful", "succeeded", "paid", "success", "completed"}
        if status_norm not in success_statuses:
            logger.info(
                "bepaid_webhook non-final status: %s (tracking_id=%s)",
                status_norm,
                tracking_id,
            )
            return web.json_response({"ok": True})

        try:
            # Credit tokens
            await user_service.add_tokens_by_telegram_id(
                telegram_id=telegram_id,
                amount=int(tokens),
                reason=LedgerReasonEnum.purchase_stars,
            )
        except Exception:
            logger.exception(
                "bepaid_webhook credit_failed user=%s tokens=%s", telegram_id, tokens
            )

        try:
            user = await user_service.get_user(telegram_id)
            balance = user.balance if user else None
            balance_text = f"*{balance}*" if balance is not None else "обновлён"
            await bot.send_message(
                telegram_id,
                text=(
                    f"✅ Оплата прошла успешно! Зачислено {tokens} токенов.\n\n"
                    f"🪙 Твой баланс: {balance_text} токенов\n\n"
                    "👇 Что хочешь сделать?"
                ),
                reply_markup=start_keyboard(BotModeEnum.passive),
            )
        except Exception:
            logger.exception("bepaid_webhook notify_failed user=%s", telegram_id)

        return web.json_response({"ok": True})

    async def veo_handle(request: web.Request):
        user_id = request.query.get("user_id")
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"status": "bad json"}, status=400)

        code = body.get("code")
        data = body.get("data") or {}
        info = data.get("info") or {}
        # In callbacks, resultUrls is JSON array or direct array depending on docs; try both
        result_urls: list[str] = []
        try:
            ru = info.get("resultUrls")
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
                msg = body.get("msg") or "Генерация не удалась"
                await bot.send_message(user_id, f"☹️ {msg}")
        except Exception:
            logger.exception("Error sending Veo video to user %s", user_id)

        return web.json_response({"ok": True})

    async def kie_nano_handle(request: web.Request):
        user_id = request.query.get("user_id")
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"status": "bad json"}, status=400)

        code = body.get("code")
        data = body.get("data") or {}
        state = data.get("state")
        result_json = data.get("resultJson")
        result_urls: list[str] = []
        try:
            if result_json:
                parsed = json.loads(result_json)
                result_urls = parsed.get("resultUrls") or []
        except Exception:
            result_urls = []

        if not user_id:
            return web.json_response({"ok": False, "error": "no user_id"}, status=400)

        try:
            if code == 200 and state == "success" and result_urls:
                caption = "Твоё изображение готово!\n\n✨ Cоздано с помощью [Vento](https://t.me/vento_toolbot)"
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

    async def suno_handle(request: web.Request):
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

    webhooks_app.router.add_post("/yookassa", yookassa_handle)
    webhooks_app.router.add_post("/bepaid", bepaid_handle)
    webhooks_app.router.add_post("/kie-image", kie_image_handle)
    webhooks_app.router.add_post("/kie-nano", kie_nano_handle)
    webhooks_app.router.add_post("/suno", suno_handle)
    webhooks_app.router.add_post("/veo", veo_handle)

    app.add_subapp("/webhooks", webhooks_app)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", settings.WEB_PORT)
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
