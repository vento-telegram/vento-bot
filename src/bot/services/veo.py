import asyncio
import json
from typing import Final

from aiohttp import ClientSession
from aiogram.types import Message

from bot.enums import BotModeEnum, LedgerReasonEnum
from bot.errors import InsufficientBalanceError, OpenAIBadRequestError
from bot.interfaces.services.veo import AbcVeoService
from bot.interfaces.services.pricing import AbcPricingService
from bot.interfaces.uow import AbcUnitOfWork
from bot.schemas import GPTMessageResponse
from bot.settings import settings


class VeoService(AbcVeoService):
    _GENERATE_URL: Final[str] = "https://nexusapi.dev/generate"
    _TASK_URL_TPL: Final[str] = "https://nexusapi.dev/tasks/{task_id}"

    def __init__(self, uow: AbcUnitOfWork, pricing_service: AbcPricingService):
        self._uow = uow
        self._pricing = pricing_service

    async def process_request(self, message: Message) -> GPTMessageResponse:
        async with self._uow:
            user = await self._uow.user.get_by_telegram_id(message.from_user.id)
            price = await self._pricing.get_price_for_mode(BotModeEnum.veo)
            if user.balance < price:
                raise InsufficientBalanceError
            updated_user = await self._uow.user.update_balance_by_user_id(user.id, -price)
            created_ledger = await self._uow.ledger.add(
                # type: ignore[name-defined]
                # Import locally to avoid circular imports
                __import__("bot.entities.ledger").bot.entities.ledger.LedgerEntity(
                    user_id=user.id, delta=-price, reason=LedgerReasonEnum.veo_video, meta=message.text
                )
            )

        if message.photo:
            file = await message.bot.get_file(message.photo[-1].file_id)
            image_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file.file_path}"
            prompt = message.caption or "Animate this photo"
        else:
            image_url = None
            prompt = message.text or ""

        payload: dict = {"params": {"prompt": prompt, "model_name": "veo-3-fast", "translate": True}}
        if image_url:
            payload["params"]["image_url"] = image_url

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {settings.VEO.NEXUS_API_KEY}",
        }

        async with ClientSession(headers=headers) as session:
            async with session.post(self._GENERATE_URL, json=payload) as resp:
                resp.raise_for_status()
                start_json = await resp.json()
                task_id = start_json.get("task_id")
                if not task_id:
                    raise OpenAIBadRequestError

            result: dict | None = None
            task_url = self._TASK_URL_TPL.format(task_id=task_id)
            for _ in range(120):
                async with session.get(task_url) as r2:
                    r2.raise_for_status()
                    data = await r2.json()
                status = data.get("status")
                if status == "completed":
                    result = data.get("result")
                    break
                if status == "failed":
                    raise OpenAIBadRequestError
                await asyncio.sleep(5)

        if not result:
            raise OpenAIBadRequestError

        video_url = result.get("video_url")
        if not video_url:
            raise OpenAIBadRequestError

        response = GPTMessageResponse(video_url=video_url)
        try:
            meta_json = json.dumps({prompt: video_url}, ensure_ascii=False)
            async with self._uow:
                await self._uow.ledger.update_meta_by_id(created_ledger.id, meta_json)  # type: ignore[arg-type]
        except Exception:
            pass

        return response


