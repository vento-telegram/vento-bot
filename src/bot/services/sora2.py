import json
import logging
from typing import Any

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiohttp import ClientSession

from bot.entities.transaction import TransactionEntity
from bot.entities.user import UserEntity
from bot.enums import TransactionReasonEnum
from bot.errors import InsufficientBalanceError
from bot.interfaces.services.sora2 import AbcSora2Service
from bot.interfaces.services.settings import AbcSettingsService
from bot.interfaces.uow import AbcUnitOfWork
from bot.settings import settings

logger = logging.getLogger(__name__)


class Sora2Service(AbcSora2Service):
    def __init__(self, uow: AbcUnitOfWork, settings_service: AbcSettingsService):
        self._uow = uow
        self._settings_service = settings_service

    async def submit_sora2_request(
        self,
        message: Message,
        state: FSMContext,
        user: UserEntity,
        prompt: str,
        image_urls: list[str] | None,
        aspect_ratio: str,
    ) -> None:
        price_str = await self._settings_service.get_value("sora2_video_price")
        request_price = int(price_str or 0)
        if user.balance < request_price:
            raise InsufficientBalanceError

        # Map UI aspect to Sora's API values
        sora_aspect = "landscape" if aspect_ratio == "16:9" else "portrait"

        # Build payload for KIE jobs API
        model_name = "sora-2-image-to-video" if (image_urls and len(image_urls) > 0) else "sora-2-text-to-video"
        input_obj: dict[str, Any] = {
            "prompt": prompt,
            "aspect_ratio": sora_aspect,
            "remove_watermark": True,
        }
        if image_urls:
            input_obj["image_urls"] = image_urls

        payload = {
            "model": model_name,
            "input": input_obj,
            "callBackUrl": self._build_callback_url(user.telegram_id),
        }

        headers = {
            "Authorization": f"Bearer {settings.KIE.API_KEY}",
            "Content-Type": "application/json",
        }
        url = f"{settings.KIE.BASE_URL}/api/v1/jobs/createTask"

        async with ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                result = await resp.json()
                if resp.status != 200 or result.get("code") != 200:
                    msg = (result.get("msg") or "Произошла ошибка при создании задачи").strip()
                    low = msg.lower()
                    if "photorealistic" in low and "people" in low:
                        # Sora policy error on photorealistic people in uploads
                        await message.answer(
                            (
                                "🚫 Sora 2 не принимает изображения с фотореалистичными людьми.\n\n"
                                "Что можно сделать:\n"
                                "• убрать людей/лица с фото или размыть/замазать их;\n"
                                "• использовать рисунок/иллюстрацию вместо фотографии;\n"
                                "• отправить только текстовое описание без изображения.\n\n"
                                "После правки просто пришли запрос ещё раз."
                            ),
                            parse_mode=None,
                        )
                    else:
                        await message.answer(f"Упс, не удалось создать задачу Sora 2: {msg}", parse_mode=None)
                    return
                data = (result or {}).get("data") or {}
                task_id = data.get("taskId")

        await self._charge(user.id, request_price, task_id, prompt, aspect_ratio, image_urls or [])

    async def _charge(self, user_id: int, price: int, task_id: str | None, prompt: str, aspect_ratio: str, image_urls: list[str]) -> None:
        async with self._uow:
            await self._uow.user.update_balance_by_user_id(user_id, -price)
            meta = json.dumps({
                "task_id": task_id,
                "prompt": prompt,
                "aspectRatio": aspect_ratio,
                "imageUrls": image_urls or [],
            }, ensure_ascii=False)
            await self._uow.transaction.add(
                TransactionEntity(user_id=user_id, delta=-price, reason=TransactionReasonEnum.sora2_request, meta=meta)
            )

    def _build_callback_url(self, telegram_id: int) -> str:
        base = settings.WEBHOOKS.BASE_URL
        if not base:
            return f"/webhooks/sora2?user_id={telegram_id}"
        return f"{base}/webhooks/sora2?user_id={telegram_id}"

