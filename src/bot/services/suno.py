import json
import logging
from typing import Any

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiohttp import ClientSession

from bot.constants import settings_models_mapper
from bot.entities.transaction import TransactionEntity
from bot.entities.user import UserEntity
from bot.enums import BotModeEnum, TransactionReasonEnum
from bot.errors import InsufficientBalanceError
from bot.interfaces.services.settings import AbcSettingsService
from bot.interfaces.services.suno import AbcSunoService
from bot.interfaces.uow import AbcUnitOfWork
from bot.settings import settings

logger = logging.getLogger(__name__)


class SunoService(AbcSunoService):
    def __init__(self, uow: AbcUnitOfWork, settings_service: AbcSettingsService):
        self._uow = uow
        self._settings_service = settings_service

    async def submit_suno_request(
        self,
        message: Message,
        state: FSMContext,
        user: UserEntity,
        style: str,
        prompt: str,
        instrumental: bool,
        custom_mode: bool,
    ) -> None:
        request_price = int(await self._settings_service.get_value(settings_models_mapper[BotModeEnum.suno_music]))
        if user.balance < request_price:
            raise InsufficientBalanceError

        payload: dict[str, Any] = {
            "prompt": prompt,
            "customMode": custom_mode,
            "instrumental": instrumental,
            "model": "V4_5PLUS",
            "callBackUrl": self._build_callback_url(user.telegram_id),
        }
        if custom_mode:
            payload["style"] = style
            payload["title"] = "@vento_toolbot song"

        headers = {
            "Authorization": f"Bearer {settings.KIE.API_KEY}",
            "Content-Type": "application/json",
        }
        url = f"{settings.KIE.BASE_URL}/api/v1/generate"

        async with ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                result = await resp.json()
                if resp.status != 200 or result.get("code") != 200:
                    msg = result.get("msg") or "Ошибка генерации"
                    await message.answer(f"☹️ Не удалось отправить задачу генерации: {msg}")
                    return
                task_id = ((result or {}).get("data") or {}).get("taskId")

        await self._charge(user.id, request_price, task_id, style if custom_mode else None, prompt, instrumental, custom_mode)
        await message.answer(
            "🎶 Начал генерацию композиции. Пришлю трек, как только он будет готов. Это займёт несколько минут."
        )

    async def _charge(self, user_id: int, price: int, task_id: str | None, style: str | None, prompt: str, instrumental: bool, custom_mode: bool) -> None:
        async with self._uow:
            updated_user = await self._uow.user.update_balance_by_user_id(user_id, -price)
            meta = json.dumps({
                "task_id": task_id,
                "style": style,
                "prompt": prompt,
                "instrumental": instrumental,
                "customMode": custom_mode,
            }, ensure_ascii=False)
            await self._uow.transaction.add(
                TransactionEntity(user_id=user_id, delta=-price, reason=TransactionReasonEnum.suno_request, meta=meta)
            )

    def _build_callback_url(self, telegram_id: int) -> str:
        base = settings.WEBHOOKS.BASE_URL
        if not base:
            return f"/webhooks/suno?user_id={telegram_id}"
        return f"{base}/webhooks/suno?user_id={telegram_id}"


