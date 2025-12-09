import asyncio
import json
import logging
from typing import Any
from urllib.parse import urlencode

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
        charge_improved = (quality == "improved") or (aspect_ratio == "9:16")
        price_key = "veo_improved_price" if charge_improved else "veo_standard_price"
        request_price = int(await self._settings_service.get_value(price_key))
        if user.balance < request_price:
            raise InsufficientBalanceError

        base_url = settings.KIE.BASE_URL.rstrip("/") if getattr(settings, "KIE", None) else "https://api.kie.ai"
        url = f"{base_url}/api/v1/veo/generate"
        headers = {
            "Authorization": f"Bearer {settings.KIE.API_KEY}",
            "Content-Type": "application/json",
        }
        generation_type = "REFERENCE_2_VIDEO" if image_urls else "TEXT_2_VIDEO"
        model_name = "veo3" if quality == "improved" else "veo3_fast"
        callback_url = self._build_callback_url(user.telegram_id, quality, aspect_ratio)
        payload: dict[str, Any] = {
            "prompt": prompt,
            "model": model_name,
            "enableTranslation": True,
            "enableFallback": enable_fallback,
            "generationType": generation_type,
            "aspectRatio": aspect_ratio,
            "callBackUrl": callback_url,
        }
        if image_urls:
            payload["imageUrls"] = image_urls
        if watermark:
            payload["watermark"] = watermark

        logger.info(
            "veo_request_start",
            extra={
                "user_id": user.id,
                "quality": quality,
                "aspect_ratio": aspect_ratio,
                "price": request_price,
                "model_name": model_name,
                "provider": "kie",
                "generation_type": generation_type,
            },
        )

        request_timeout = ClientTimeout(total=30)
        try:
            async with ClientSession(timeout=request_timeout) as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    try:
                        result = await resp.json()
                    except Exception:
                        raw_text = await resp.text()
                        result = {"msg": raw_text}

                    status_ok = resp.status == 200
                    code_ok = (result.get("code") in (200, "200")) if isinstance(result, dict) else False
                    if not (status_ok and code_ok):
                        msg = (
                            result.get("msg")
                            or result.get("message")
                            or result.get("error")
                            or "Сервис вернул ошибку при запуске генерации"
                        )
                        await message.answer(f"☹️ Не удалось запустить генерацию Veo3: {msg}")
                        logger.warning(
                            "veo_request_failed_to_start",
                            extra={"user_id": user.id, "status": resp.status, "error_msg": msg},
                        )
                        return

                    data = result.get("data") or {}
                    task_id = data.get("taskId") or data.get("task_id") or data.get("id")
                    if not task_id:
                        await message.answer("☹️ Не удалось получить идентификатор задачи в KIE.")
                        logger.warning("veo_request_no_task_id", extra={"user_id": user.id, "payload": result})
                        return
        except (ClientError, asyncio.TimeoutError):
            await message.answer("☹️ Не удалось связаться с KIE. Попробуй ещё раз позже.")
            logger.exception("veo_request_network_error", extra={"user_id": user.id})
            return

        logger.info("veo_request_task_created", extra={"user_id": user.id, "task_id": task_id})
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

    def _build_callback_url(self, telegram_id: int, quality: str, aspect_ratio: str) -> str:
        params = {"user_id": telegram_id}
        if quality:
            params["quality"] = quality
        if aspect_ratio:
            params["aspect"] = aspect_ratio
        query = urlencode(params, doseq=False)
        base = (settings.WEBHOOKS.BASE_URL or "").rstrip("/")
        path = f"/webhooks/veo?{query}"
        return f"{base}{path}" if base else path


