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
from bot.interfaces.services.sora2_pro import AbcSora2ProService
from bot.interfaces.services.settings import AbcSettingsService
from bot.interfaces.uow import AbcUnitOfWork
from bot.settings import settings

logger = logging.getLogger(__name__)


class Sora2ProService(AbcSora2ProService):
    def __init__(self, uow: AbcUnitOfWork, settings_service: AbcSettingsService):
        self._uow = uow
        self._settings_service = settings_service

    async def submit_sora2_pro_request(
        self,
        message: Message,
        state: FSMContext,
        user: UserEntity,
        prompt: str,
        image_urls: list[str] | None,
        aspect_ratio: str,
        n_frames: str,
    ) -> None:
        price_str = await self._settings_service.get_value("sora2_pro_video_price")
        request_price = None
        try:
            request_price = int(price_str) if price_str is not None else 150
        except Exception:
            request_price = 150
        if user.balance < request_price:
            raise InsufficientBalanceError

        # Map UI aspect to Sora Pro API values
        sora_aspect = "landscape" if aspect_ratio == "16:9" else "portrait"

        # Validate n_frames
        n_frames_val = "15" if str(n_frames) == "15" else "10"

        # Build payload for KIE jobs API
        model_name = (
            "sora-2-pro-image-to-video" if (image_urls and len(image_urls) > 0) else "sora-2-pro-text-to-video"
        )
        input_obj: dict[str, Any] = {
            "prompt": prompt,
            "aspect_ratio": sora_aspect,
            "n_frames": n_frames_val,
            "size": "standard",
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

        # Pre-charge with atomic debit
        preview_meta = json.dumps(
            {
                "prompt": prompt,
                "aspectRatio": aspect_ratio,
                "nFrames": n_frames_val,
                "imageUrls": image_urls or [],
            },
            ensure_ascii=False,
        )
        async with self._uow:
            updated_user = await self._uow.user.try_debit(user.id, request_price)
            if not updated_user:
                raise InsufficientBalanceError
            await self._uow.transaction.add(
                TransactionEntity(
                    user_id=user.id,
                    delta=-request_price,
                    reason=TransactionReasonEnum.sora2_request,
                    meta=preview_meta,
                )
            )

        async with ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                result = await resp.json()
                if resp.status != 200 or result.get("code") != 200:
                    msg = (result.get("msg") or "").strip()
                    low = msg.lower()
                    if "photorealistic" in low and "people" in low:
                        await message.answer(
                            (
                                "📵 Sora 2 запрещает изображения с фотореалистичными людьми.\n\n"
                                "Попробуйте вместо этого:\n"
                                "- Другую иллюстрацию без людей/лиц;\n"
                                "- Сменить запрос, чтобы не затрагивать внешность реальных людей;\n"
                                "- Использовать только текстовый запрос без изображения.\n\n"
                                "Если вы уверены, что это ошибка — напишите в поддержку."
                            ),
                            parse_mode=None,
                        )
                    elif ("violate" in low and "polic" in low) or ("content may violate openai" in low):
                        await message.answer(
                            (
                                "⚠️ Контент может нарушать политики OpenAI.\n\n"
                                "Переформулируйте запрос, избегая чувствительных тем, и попробуйте снова."
                            ),
                            parse_mode=None,
                        )
                    else:
                        await message.answer(f"Ошибка при запуске Sora 2 Pro: {msg}", parse_mode=None)
                    await self._refund(user.id, request_price, prompt, aspect_ratio, n_frames_val, image_urls or [])
                    return
                # success: nothing more to do here; webhook will deliver the result

    async def _refund(
        self, user_id: int, price: int, prompt: str, aspect_ratio: str, n_frames: str, image_urls: list[str]
    ) -> None:
        meta = json.dumps(
            {
                "prompt": prompt,
                "aspectRatio": aspect_ratio,
                "nFrames": n_frames,
                "imageUrls": image_urls or [],
            },
            ensure_ascii=False,
        )
        async with self._uow:
            await self._uow.user.update_balance_by_user_id(user_id, +price)
            await self._uow.transaction.add(
                TransactionEntity(user_id=user_id, delta=+price, reason=TransactionReasonEnum.sora2_refund, meta=meta)
            )

    def _build_callback_url(self, telegram_id: int) -> str:
        base = settings.WEBHOOKS.BASE_URL
        if not base:
            return f"/webhooks/sora2?user_id={telegram_id}"
        return f"{base}/webhooks/sora2?user_id={telegram_id}"

