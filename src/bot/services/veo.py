import json
import logging
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
        if quality == 'improved':
            price_key = 'veo_improved_price'
        else:
            price_key = 'veo_standard_price'
        request_price = int(await self._settings_service.get_value(price_key))
        if user.balance < request_price:
            raise InsufficientBalanceError

        payload: dict[str, Any] = {
            "prompt": prompt,
            "model": "veo3" if quality == 'improved' else "veo3_fast",
            "aspectRatio": aspect_ratio,
            "enableFallback": bool(enable_fallback),
            "enableTranslation": True,
            "callBackUrl": self._build_callback_url(user.telegram_id),
        }
        if image_urls:
            payload["imageUrls"] = image_urls
        if watermark:
            payload["watermark"] = watermark

        headers = {
            "Authorization": f"Bearer {settings.KIE.API_KEY}",
            "Content-Type": "application/json",
        }
        url = f"{settings.KIE.BASE_URL}/api/v1/veo/generate"

        async with ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                result = await resp.json()
                if resp.status != 200 or result.get("code") != 200:
                    msg = result.get("msg") or "Ошибка генерации"
                    await message.answer(f"☹️ Не удалось отправить задачу генерации видео: {msg}")
                    return
                task_id = ((result or {}).get("data") or {}).get("taskId")

        await self._charge(user.id, request_price, task_id, prompt, aspect_ratio, quality, image_urls)

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


