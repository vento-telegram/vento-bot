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
from bot.interfaces.services.settings import AbcSettingsService
from bot.interfaces.services.suno import AbcSunoService
from bot.interfaces.uow import AbcUnitOfWork
from bot.settings import settings

logger = logging.getLogger(__name__)


class SunoService(AbcSunoService):
    def __init__(self, uow: AbcUnitOfWork, settings_service: AbcSettingsService):
        self._uow = uow
        self._settings_service = settings_service

    async def submit_generate_music(self, message: Message, state: FSMContext, user: UserEntity) -> None:
        state_data = await state.get_data()
        suno = state_data.get("suno", {}) or {}
        prompt = (message.text or "").strip()
        if not prompt:
            await message.answer("✍️ Отправь текстовый промпт для генерации музыки.")
            return

        request_price = int(await self._settings_service.get_value(settings_models_mapper[BotModeEnum.suno]))
        if user.balance < request_price:
            raise InsufficientBalanceError

        payload: dict[str, Any] = {
            "prompt": prompt[:5000],
            "customMode": bool(suno.get("customMode", False)),
            "instrumental": bool(suno.get("instrumental", True)),
            "model": (suno.get("model") or "V3_5"),
            "callBackUrl": self._build_callback_url(message.from_user.id, "suno-generate"),
        }
        # Optional fields
        for key in ("style", "title", "negativeTags", "vocalGender"):
            if suno.get(key):
                payload[key] = suno[key]
        for key in ("styleWeight", "weirdnessConstraint", "audioWeight"):
            v = suno.get(key)
            if isinstance(v, (int, float)):
                payload[key] = v

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
                    await message.answer(f"☹️ Не удалось отправить задачу: {msg}")
                    return
                task_id = ((result or {}).get("data") or {}).get("taskId")

        await self._charge(user.id, request_price, LedgerReasonEnum.suno_request, json.dumps({
            "task_id": task_id,
            "action": "generate",
            "payload": payload,
        }, ensure_ascii=False))

        await message.answer(
            "🎵 Задача отправлена в Suno. Пришлю треки, как только они будут готовы."
        )

    async def submit_extend_music(self, message: Message, state: FSMContext, user: UserEntity) -> None:
        state_data = await state.get_data()
        suno = state_data.get("suno", {}) or {}
        audio_id = (message.text or "").strip()
        if not audio_id:
            await message.answer("Вставь audioId трека, который нужно продолжить.")
            return

        request_price = int(await self._settings_service.get_value(settings_models_mapper[BotModeEnum.suno]))
        if user.balance < request_price:
            raise InsufficientBalanceError

        payload: dict[str, Any] = {
            "audioId": audio_id,
            # Use original params by default for simplicity
            "defaultParamFlag": False,
            "model": (suno.get("model") or "V3_5"),
            "callBackUrl": self._build_callback_url(message.from_user.id, "suno-extend"),
        }

        headers = {
            "Authorization": f"Bearer {settings.KIE.API_KEY}",
            "Content-Type": "application/json",
        }
        url = f"{settings.KIE.BASE_URL}/api/v1/generate/extend"

        async with ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                result = await resp.json()
                if resp.status != 200 or result.get("code") != 200:
                    msg = result.get("msg") or "Ошибка расширения трека"
                    await message.answer(f"☹️ Не удалось отправить задачу: {msg}")
                    return
                task_id = ((result or {}).get("data") or {}).get("taskId")

        await self._charge(user.id, request_price, LedgerReasonEnum.suno_request, json.dumps({
            "task_id": task_id,
            "action": "extend",
            "audio_id": audio_id,
        }, ensure_ascii=False))

        await message.answer("➕ Продление трека отправлено. Пришлю результат, как только будет готов.")

    async def submit_add_instrumental(self, message: Message, state: FSMContext, user: UserEntity) -> None:
        state_data = await state.get_data()
        suno = state_data.get("suno", {}) or {}
        upload_url = suno.get("uploadUrl")
        title = suno.get("title")
        tags = suno.get("tags")
        negative = suno.get("negativeTags")

        # If expecting audio, try to obtain URL from message
        if not upload_url:
            upload_url = await self._maybe_extract_audio_url(message)
            if upload_url:
                suno["uploadUrl"] = upload_url
                await state.update_data(suno=suno)

        if not upload_url or not title or not tags or not negative:
            await message.answer("Проверь, что указаны аудио, заголовок, теги и негатив‑теги.")
            return

        request_price = int(await self._settings_service.get_value(settings_models_mapper[BotModeEnum.suno]))
        if user.balance < request_price:
            raise InsufficientBalanceError

        payload: dict[str, Any] = {
            "uploadUrl": upload_url,
            "title": title,
            "tags": tags,
            "negativeTags": negative,
            "callBackUrl": self._build_callback_url(message.from_user.id, "suno-instrumental"),
        }
        for key in ("vocalGender",):
            if suno.get(key):
                payload[key] = suno[key]
        for key in ("styleWeight", "weirdnessConstraint", "audioWeight"):
            v = suno.get(key)
            if isinstance(v, (int, float)):
                payload[key] = v

        headers = {
            "Authorization": f"Bearer {settings.KIE.API_KEY}",
            "Content-Type": "application/json",
        }
        url = f"{settings.KIE.BASE_URL}/api/v1/generate/add-instrumental"

        async with ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                result = await resp.json()
                if resp.status != 200 or result.get("code") != 200:
                    msg = result.get("msg") or "Ошибка генерации инструментала"
                    await message.answer(f"☹️ Не удалось отправить задачу: {msg}")
                    return
                task_id = ((result or {}).get("data") or {}).get("taskId")

        await self._charge(user.id, request_price, LedgerReasonEnum.suno_request, json.dumps({
            "task_id": task_id,
            "action": "add_instrumental",
            "upload_url": upload_url,
        }, ensure_ascii=False))

        await message.answer("🎶 Отправил задачу на генерацию инструментала. Жду результат.")

    async def submit_add_vocals(self, message: Message, state: FSMContext, user: UserEntity) -> None:
        state_data = await state.get_data()
        suno = state_data.get("suno", {}) or {}
        upload_url = suno.get("uploadUrl") or await self._maybe_extract_audio_url(message)
        if upload_url:
            suno["uploadUrl"] = upload_url
            await state.update_data(suno=suno)
        prompt = suno.get("prompt") or (message.text or "").strip()
        title = suno.get("title")
        style = suno.get("style")
        negative = suno.get("negativeTags")
        if not upload_url or not prompt or not title or not style or not negative:
            await message.answer("Нужно указать аудио, промпт, заголовок, стиль и негатив‑теги.")
            return

        request_price = int(await self._settings_service.get_value(settings_models_mapper[BotModeEnum.suno]))
        if user.balance < request_price:
            raise InsufficientBalanceError

        payload: dict[str, Any] = {
            "prompt": prompt[:5000],
            "title": title,
            "style": style,
            "negativeTags": negative,
            "uploadUrl": upload_url,
            "callBackUrl": self._build_callback_url(message.from_user.id, "suno-vocals"),
        }
        for key in ("vocalGender",):
            if suno.get(key):
                payload[key] = suno[key]
        for key in ("styleWeight", "weirdnessConstraint", "audioWeight"):
            v = suno.get(key)
            if isinstance(v, (int, float)):
                payload[key] = v

        headers = {
            "Authorization": f"Bearer {settings.KIE.API_KEY}",
            "Content-Type": "application/json",
        }
        url = f"{settings.KIE.BASE_URL}/api/v1/generate/add-vocals"

        async with ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                result = await resp.json()
                if resp.status != 200 or result.get("code") != 200:
                    msg = result.get("msg") or "Ошибка добавления вокала"
                    await message.answer(f"☹️ Не удалось отправить задачу: {msg}")
                    return
                task_id = ((result or {}).get("data") or {}).get("taskId")

        await self._charge(user.id, request_price, LedgerReasonEnum.suno_request, json.dumps({
            "task_id": task_id,
            "action": "add_vocals",
            "upload_url": upload_url,
        }, ensure_ascii=False))

        await message.answer("🎤 Задача по добавлению вокала отправлена. Жду результат.")

    async def submit_generate_lyrics(self, message: Message, state: FSMContext, user: UserEntity) -> None:
        prompt = (message.text or "").strip()
        if not prompt:
            await message.answer("✍️ Отправь описание/тему для текста песни.")
            return

        request_price = int(await self._settings_service.get_value(settings_models_mapper[BotModeEnum.suno]))
        if user.balance < request_price:
            raise InsufficientBalanceError

        payload = {
            "prompt": prompt[:1000],
            "callBackUrl": self._build_callback_url(message.from_user.id, "suno-lyrics"),
        }
        headers = {
            "Authorization": f"Bearer {settings.KIE.API_KEY}",
            "Content-Type": "application/json",
        }
        url = f"{settings.KIE.BASE_URL}/api/v1/lyrics"

        async with ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                result = await resp.json()
                if resp.status != 200 or result.get("code") != 200:
                    msg = result.get("msg") or "Ошибка генерации текста"
                    await message.answer(f"☹️ Не удалось отправить задачу: {msg}")
                    return
                task_id = ((result or {}).get("data") or {}).get("taskId")

        await self._charge(user.id, request_price, LedgerReasonEnum.suno_request, json.dumps({
            "task_id": task_id,
            "action": "lyrics",
        }, ensure_ascii=False))

        await message.answer("📜 Отправил задачу на написание текста. Пришлю результат.")

    async def submit_vocal_separation(self, message: Message, state: FSMContext, user: UserEntity) -> None:
        state_data = await state.get_data()
        suno = state_data.get("suno", {}) or {}
        task_id = suno.get("sep_taskId")
        audio_id = suno.get("sep_audioId")
        sep_type = suno.get("sep_type") or "separate_vocal"
        if not task_id or not audio_id:
            await message.answer("Укажи taskId и audioId для раздельного экспорта дорожек.")
            return

        request_price = int(await self._settings_service.get_value(settings_models_mapper[BotModeEnum.suno]))
        if user.balance < request_price:
            raise InsufficientBalanceError

        payload = {
            "taskId": task_id,
            "audioId": audio_id,
            "type": sep_type,
            "callBackUrl": self._build_callback_url(message.from_user.id, "suno-vocal-separation"),
        }
        headers = {
            "Authorization": f"Bearer {settings.KIE.API_KEY}",
            "Content-Type": "application/json",
        }
        url = f"{settings.KIE.BASE_URL}/api/v1/vocal-removal/generate"

        async with ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                result = await resp.json()
                if resp.status != 200 or result.get("code") != 200:
                    msg = result.get("msg") or "Ошибка разделения дорожек"
                    await message.answer(f"☹️ Не удалось отправить задачу: {msg}")
                    return

        await self._charge(user.id, request_price, LedgerReasonEnum.suno_request, json.dumps({
            "action": "vocal_separation",
            "task_id": task_id,
            "audio_id": audio_id,
            "type": sep_type,
        }, ensure_ascii=False))

        await message.answer("🎚️ Разделение дорожек запущено. Пришлю ссылки на файлы.")

    async def _charge(self, user_id: int, amount: int, reason: LedgerReasonEnum, meta: str | None):
        async with self._uow:
            updated_user = await self._uow.user.update_balance_by_user_id(user_id, -amount)
            await self._uow.ledger.add(
                LedgerEntity(user_id=user_id, delta=-amount, reason=reason, meta=meta)
            )
            return updated_user

    def _build_callback_url(self, telegram_id: int, path: str) -> str:
        base = settings.KIE.CALLBACK_BASE
        if not base:
            return f"/webhooks/suno/{path}?user_id={telegram_id}"
        return f"{base}/webhooks/suno/{path}?user_id={telegram_id}"

    async def _maybe_extract_audio_url(self, message: Message) -> str | None:
        try:
            bot = message.bot
            if message.audio:
                file = await bot.get_file(message.audio.file_id)
                return f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
            if message.voice:
                file = await bot.get_file(message.voice.file_id)
                return f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
            if message.document and (message.document.mime_type or "").lower().startswith("audio/"):
                file = await bot.get_file(message.document.file_id)
                return f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
        except Exception:
            logger.exception("Failed to get telegram file url")
        return None


