import json
import logging
import asyncio
from typing import Any

from aiohttp import ClientSession

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.constants import settings_models_mapper
from bot.entities.ledger import LedgerEntity
from bot.entities.user import UserEntity
from bot.enums import BotModeEnum, LedgerReasonEnum
from bot.errors import InsufficientBalanceError
from bot.interfaces.services.veo import AbcVeoService
from bot.interfaces.services.settings import AbcSettingsService
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
        # Determine price based on quality
        price_key = 'veo_improved_price' if quality == 'improved' else 'veo_standard_price'
        request_price = int(await self._settings_service.get_value(price_key))
        if user.balance < request_price:
            raise InsufficientBalanceError

        # Build Nexus payload (see veo3bot example)
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

        async with ClientSession(headers=headers) as session:
            # Step 1: create generation task
            start_url = f"{base_url}/generate"
            async with session.post(start_url, json={'params': params}) as resp:
                data = await resp.json()
                if resp.status != 200 or 'task_id' not in data:
                    msg = data.get('message') or data.get('error') or 'Ошибка запуска генерации'
                    await message.answer(f"☹️ Не удалось запустить генерацию видео: {msg}")
                    return
                task_id = data['task_id']

            # Charge immediately after task creation (same behavior as with KIE)
            await self._charge(user.id, request_price, task_id, prompt, aspect_ratio, quality, image_urls)

            # Step 2: poll for result
            poll_url = f"{base_url}/tasks/{task_id}"
            video_url: str | None = None
            while True:
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
                        return
                await asyncio.sleep(10)

            if not video_url:
                await message.answer("☹️ Не удалось получить ссылку на видео.")
                return

            # Optional: change aspect ratio if needed
            if aspect_ratio and aspect_ratio != '16:9':
                ratio_payload = {
                    'params': {
                        'model_name': 'veo-ratio',
                        'video_url': video_url,
                        'aspect_ratio': aspect_ratio,
                    }
                }
                async with session.post(start_url, json=ratio_payload) as r_resp:
                    r_data = await r_resp.json()
                    if r_resp.status == 200 and 'task_id' in r_data:
                        r_task_id = r_data['task_id']
                        r_poll_url = f"{base_url}/tasks/{r_task_id}"
                        while True:
                            async with session.get(r_poll_url) as r_poll:
                                r_json = await r_poll.json()
                                r_status = r_json.get('status')
                                if r_status == 'completed':
                                    r_result = r_json.get('result') or {}
                                    video_url = r_result.get('video_url') or video_url
                                    break
                                if r_status == 'failed':
                                    # Keep original video if ratio failed
                                    break
                            await asyncio.sleep(10)

            # Send result to user
            caption = "🎬 Вот твоё видео!\n\n✨ Cоздано с помощью [Vento](https://t.me/vento_toolbot)"
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
            await self._uow.ledger.add(
                LedgerEntity(user_id=user_id, delta=-price, reason=LedgerReasonEnum.veo_request, meta=meta)
            )

    def _build_callback_url(self, telegram_id: int) -> str:
        base = settings.KIE.CALLBACK_BASE
        if not base:
            return f"/webhooks/veo?user_id={telegram_id}"
        return f"{base}/webhooks/veo?user_id={telegram_id}"


