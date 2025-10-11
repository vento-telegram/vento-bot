import asyncio
import json
import logging
import time
from typing import Any

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiohttp import ClientError, ClientSession, ClientTimeout

from bot.entities.transaction import TransactionEntity
from bot.entities.user import UserEntity
from bot.enums import TransactionReasonEnum
from bot.errors import InsufficientBalanceError
from bot.interfaces.services.settings import AbcSettingsService
from bot.interfaces.services.veo import AbcVeoService
from bot.interfaces.uow import AbcUnitOfWork
from bot.settings import settings

logger = logging.getLogger(__name__)


class VeoService(AbcVeoService):
    def __init__(self, uow: AbcUnitOfWork, settings_service: AbcSettingsService):
        self._uow = uow
        self._settings_service = settings_service

    async def submit_veo_request(
        self,
        message: Message,
        state: FSMContext,
        user: UserEntity,
        prompt: str,
        image_urls: list[str] | None,
        aspect_ratio: str,
        quality: str,
        enable_fallback: bool,
        watermark: str | None,
    ) -> None:
        # Pricing rules:
        # - 16:9 standard => standard price
        # - 9:16 standard => improved price
        # - 16:9 improved => improved price
        # - 9:16 improved => improved price
        charge_improved = (quality == 'improved') or (aspect_ratio == '9:16')
        price_key = 'veo_improved_price' if charge_improved else 'veo_standard_price'
        request_price = int(await self._settings_service.get_value(price_key))
        if user.balance < request_price:
            raise InsufficientBalanceError

        base_url = settings.NEXUS.BASE_URL.rstrip('/') if getattr(settings, 'NEXUS', None) else "https://nexusapi.dev"
        api_key = (getattr(settings.NEXUS, 'API_KEY', None) if getattr(settings, 'NEXUS', None) else None) or ""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        model_name = 'veo-3-quality' if quality == 'improved' else 'veo-3-fast'
        params: dict[str, Any] = {
            'prompt': prompt,
            'model_name': model_name,
            'translate': True,
        }
        if image_urls and len(image_urls) > 0:
            params['image_url'] = image_urls[0]

        # Logging context
        logger.info(
            "veo_request_start",
            extra={
                "user_id": user.id,
                "quality": quality,
                "aspect_ratio": aspect_ratio,
                "price": request_price,
                "model_name": model_name,
            },
        )

        # Reasonable timeouts and polling limits
        create_timeout = ClientTimeout(total=30)
        request_timeout = ClientTimeout(total=20)
        poll_interval_sec = 10
        poll_max_seconds = 600  # 10 minutes
        ratio_poll_max_seconds = 300  # 5 minutes

        async with ClientSession(headers=headers, timeout=request_timeout) as session:
            # Step 1: create generation task
            start_url = f"{base_url}/generate"
            try:
                async with session.post(start_url, json={'params': params}, timeout=create_timeout) as resp:
                    data = await resp.json()
                    if (resp.status < 200 or resp.status >= 300):
                        msg = data.get('message') or data.get('error') or 'Ошибка запуска генерации'
                        await message.answer(f"☹️ Не удалось запустить генерацию видео: {msg}")
                        logger.warning("veo_request_failed_to_start", extra={"user_id": user.id, "status": resp.status, "msg": msg})
                        return
                    task_id = data.get('task_id') or (data.get('data') or {}).get('task_id') or data.get('id')
                    if not task_id:
                        msg = data.get('message') or data.get('error') or 'Не удалось получить идентификатор задачи'
                        await message.answer(f"☹️ Не удалось запустить генерацию видео: {msg}")
                        logger.warning("veo_request_no_task_id", extra={"user_id": user.id})
                        return
            except (ClientError, asyncio.TimeoutError):
                await message.answer("☹️ Не удалось связаться с сервисом генерации. Попробуй ещё раз позже.")
                logger.exception("veo_request_network_error", extra={"user_id": user.id})
                return

            logger.info("veo_request_task_created", extra={"user_id": user.id, "task_id": task_id})

            # Charge immediately after task creation (same behavior as with KIE)
            await self._charge(user.id, request_price, task_id, prompt, aspect_ratio, quality, image_urls)

            # Step 2: poll for result (bounded)
            poll_url = f"{base_url}/tasks/{task_id}"
            video_url: str | None = None
            poll_deadline = time.monotonic() + poll_max_seconds
            poll_started = time.monotonic()
            while time.monotonic() < poll_deadline:
                try:
                    async with session.get(poll_url) as poll_resp:
                        task_json = await poll_resp.json()
                        status = task_json.get('status')
                        if status == 'completed':
                            result = task_json.get('result') or {}
                            video_url = result.get('video_url') or result.get('url')
                            break
                        if status == 'failed':
                            err = task_json.get('error') or 'Неизвестная ошибка'
                            await message.answer(f"☹️ Генерация не удалась: {err}")
                            logger.warning("veo_request_failed_status", extra={"user_id": user.id, "task_id": task_id, "error": err})
                            try:
                                await self._refund(user.id, request_price, task_id, prompt, aspect_ratio, quality, image_urls)
                            except Exception:
                                logger.exception("veo_request_refund_failed", extra={"user_id": user.id, "task_id": task_id})
                            return
                except (ClientError, asyncio.TimeoutError):
                    # transient error, keep polling until deadline
                    logger.warning("veo_request_poll_error", extra={"user_id": user.id, "task_id": task_id})
                await asyncio.sleep(poll_interval_sec)

            if not video_url:
                await message.answer("⏳ Время ожидания генерации истекло. Попробуй ещё раз позже.")
                logger.warning("veo_request_poll_timeout", extra={"user_id": user.id, "task_id": task_id})
                try:
                    await self._refund(user.id, request_price, task_id, prompt, aspect_ratio, quality, image_urls)
                except Exception:
                    logger.exception("veo_request_refund_failed", extra={"user_id": user.id, "task_id": task_id})
                return

            total_poll_time = time.monotonic() - poll_started
            logger.info("veo_request_completed", extra={"user_id": user.id, "task_id": task_id, "elapsed_sec": round(total_poll_time, 2)})

            # Optional: change aspect ratio if needed
            ratio_failed = False
            if aspect_ratio and aspect_ratio != '16:9':
                ratio_payload = {
                    'params': {
                        'model_name': 'veo-ratio',
                        'video_url': video_url,
                        'aspect_ratio': aspect_ratio,
                    }
                }
                try:
                    async with session.post(start_url, json=ratio_payload) as r_resp:
                        r_data = await r_resp.json()
                        if (200 <= r_resp.status < 300) and 'task_id' in r_data:
                            r_task_id = r_data['task_id']
                            r_poll_url = f"{base_url}/tasks/{r_task_id}"
                            r_deadline = time.monotonic() + ratio_poll_max_seconds
                            while time.monotonic() < r_deadline:
                                try:
                                    async with session.get(r_poll_url) as r_poll:
                                        r_json = await r_poll.json()
                                        r_status = r_json.get('status')
                                        if r_status == 'completed':
                                            r_result = r_json.get('result') or {}
                                            video_url = r_result.get('video_url') or video_url
                                            logger.info("veo_ratio_completed", extra={"user_id": user.id, "task_id": task_id, "ratio_task_id": r_task_id})
                                            break
                                        if r_status == 'failed':
                                            ratio_failed = True
                                            logger.warning("veo_ratio_failed_status", extra={"user_id": user.id, "task_id": task_id, "ratio_task_id": r_task_id})
                                            break
                                except (ClientError, asyncio.TimeoutError):
                                    logger.warning("veo_ratio_poll_error", extra={"user_id": user.id, "task_id": task_id})
                                await asyncio.sleep(poll_interval_sec)
                            else:
                                ratio_failed = True
                                logger.warning("veo_ratio_poll_timeout", extra={"user_id": user.id, "task_id": task_id})
                        else:
                            ratio_failed = True
                            logger.warning("veo_ratio_start_failed", extra={"user_id": user.id, "task_id": task_id, "status": r_resp.status})
                except (ClientError, asyncio.TimeoutError):
                    ratio_failed = True
                    logger.exception("veo_ratio_network_error", extra={"user_id": user.id, "task_id": task_id})

            if aspect_ratio and aspect_ratio != '16:9' and ratio_failed:
                try:
                    await message.answer("⚠️ Не удалось конвертировать видео в 9:16. Отправляю исходный формат 16:9.")
                except Exception:
                    pass

            caption = "🎬 Твоё видео готово!\n\n✨ Создано с помощью [Vento](https://t.me/vento_toolbot)"
            try:
                await message.answer_video(video_url, caption=caption)
            except Exception:
                await message.answer(f"Готово: {video_url}")

    async def _charge(self, user_id: int, price: int, task_id: str | None, prompt: str, aspect_ratio: str, quality: str, image_urls: list[str] | None) -> None:
        async with self._uow:
            updated_user = await self._uow.user.update_balance_by_user_id(user_id, -price)
            meta = json.dumps({
                "task_id": task_id,
                "prompt": prompt,
                "aspectRatio": aspect_ratio,
                "quality": quality,
                "imageUrls": image_urls or [],
            }, ensure_ascii=False)
            await self._uow.transaction.add(
                TransactionEntity(user_id=user_id, delta=-price, reason=TransactionReasonEnum.veo_request, meta=meta)
            )
        logger.info("veo_request_charged", extra={"user_id": user_id, "task_id": task_id, "price": price})

    async def _refund(self, user_id: int, amount: int, task_id: str | None, prompt: str, aspect_ratio: str, quality: str, image_urls: list[str] | None) -> None:
        async with self._uow:
            await self._uow.user.update_balance_by_user_id(user_id, +amount)
            meta = json.dumps({
                "task_id": task_id,
                "prompt": prompt,
                "aspectRatio": aspect_ratio,
                "quality": quality,
                "imageUrls": image_urls or [],
                "refund": True,
            }, ensure_ascii=False)
            await self._uow.transaction.add(
                TransactionEntity(user_id=user_id, delta=+amount, reason=TransactionReasonEnum.veo_refund, meta=meta)
            )
        logger.info("veo_request_refunded", extra={"user_id": user_id, "task_id": task_id, "amount": amount})

    def _build_callback_url(self, telegram_id: int) -> str:
        base = settings.WEBHOOKS.BASE_URL
        if not base:
            return f"/webhooks/veo?user_id={telegram_id}"
        return f"{base}/webhooks/veo?user_id={telegram_id}"


