import logging
import re

from aiohttp import ClientSession
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from openai import OpenAI as OpenAIClient
from openai import BadRequestError as OpenAIInvalidRequestError
from openai.types import ImagesResponse

from bot.enums import BotModeEnum
from bot.errors import OpenAIBadRequestError
from bot.interfaces.services.gpt import AbcOpenAIService
from bot.interfaces.services.pricing import AbcPricingService
from bot.interfaces.uow import AbcUnitOfWork
from openai.types.chat import (
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam, ChatCompletionMessageParam, ChatCompletionContentPartTextParam,
    ChatCompletionContentPartImageParam
)

from bot.schemas import GPTMessageResponse

IMAGE_PROMPT_PATTERNS = [
    r"(?:^|\s)!draw\s*[:\-]?\s*(.+)",
    r"(?:^|\s)сгенерируй\s*(?:картинку|изображение)?\s*[:\-]?\s*(.+)",
    r"(?:^|\s)создай\s*(?:картинку|изображение)?\s*[:\-]?\s*(.+)",
    r"(?:^|\s)нарисуй\s*[:\-]?\s*(.+)",
    r"(?:^|\s)хочу\s*(?:увидеть|получить)?\s*(?:картинку|изображение)?\s*[:\-]?\s*(.+)",
    r"(?:^|\s)покажи\s*(?:мне)?\s*(?:рисунок|арт|картинку)\s*[:\-]?\s*(.+)",
    r"(?:^|\s)изобрази\s*[:\-]?\s*(.+)",
    r"(?:^|\s)(?:придумай|представь)\s*(?:и)?\s*(?:сделай|покажи)?\s*(?:картинку|сцену|изображение)\s*[:\-]?\s*(.+)",
    r"(?:^|\s)generate\s*(?:an? )?(?:image|picture|art)\s*[:\-]?\s*(.+)",
    r"(?:^|\s)draw\s*(?:me)?\s*[:\-]?\s*(.+)",
    r"(?:^|\s)make\s*(?:a|an)?\s*(?:image|picture|drawing)\s*[:\-]?\s*(.+)",
]

IMAGE_EXCLUDE_KEYWORDS = [
    "словами", "опиши", "текстом", "расскажи", "в виде текста"
]

logger = logging.getLogger(__name__)

class OpenAIService(AbcOpenAIService):
    def __init__(self, uow: AbcUnitOfWork, client: OpenAIClient, pricing_service: AbcPricingService):
        self._uow = uow
        self._client = client
        self._pricing_service = pricing_service
        self._gpt5_price_tokens = 5

    async def process_gpt_request(self, message: Message, state: FSMContext) -> GPTMessageResponse:
        history: list[ChatCompletionMessageParam] = (await state.get_data()).get("history", [])

        async with self._uow:
            user = await self._uow.user.get_by_telegram_id(message.from_user.id)

        gpt_model = "gpt-5" if user.balance >= await self._pricing_service.get_price_for_mode(BotModeEnum.gpt5) else "gpt-5-mini"

        if message.photo:
            response = await self._handle_photo(message, history, gpt_model)

        elif message.voice:
            response = await self._handle_voice(message, history, gpt_model)

        else:
            response = await self._handle_text(message, history, gpt_model)

        await state.update_data(history=history[-10:])

        return response

    async def process_dalle_request(self, message: Message, history: list[ChatCompletionMessageParam] | None = None):
        try:
            response: ImagesResponse = await self._client.images.generate(
                model="dall-e-3",
                prompt=message.text,
                size="1024x1024",
                quality="standard",
                response_format="url",
                n=1,
            )
        except OpenAIInvalidRequestError:
            raise OpenAIBadRequestError

        image_result_url = response.data[0].url
        if history is not None:
            history.append(
                ChatCompletionUserMessageParam(
                    role="user",
                    content=[ChatCompletionContentPartTextParam(type="text", text=message.text)],
                )
            )
            history.append(
                ChatCompletionAssistantMessageParam(
                    role="assistant",
                    content=[
                        ChatCompletionContentPartTextParam(type="text", text=image_result_url)],
                )
            )

        return GPTMessageResponse(image_url=image_result_url)

    async def _transcribe_audio(self, url: str) -> str:
        async with ClientSession() as session:
            async with session.get(url) as resp:
                audio_bytes = await resp.read()

        transcript = await self._client.audio.transcriptions.create(
            model="whisper-1",
            file=("voice.ogg", audio_bytes, "audio/ogg")
        )
        return transcript.text

    @staticmethod
    def _parse_image_prompt(text: str) -> str | None:
        if any(kw in text.lower() for kw in IMAGE_EXCLUDE_KEYWORDS):
            return None

        for pattern in IMAGE_PROMPT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                return next((g for g in groups if g), None)
        return None


    async def _handle_photo(self, message: Message, history, model: str):
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        url = f"https://api.telegram.org/file/bot{message.bot.token}/{file.file_path}"
        if image_prompt := self._parse_image_prompt(message.caption) if message.caption else None:
            logger.info(f"Detected image generation prompt: {image_prompt}")
            text_message = Message(**{**message.model_dump(), "text": image_prompt})
            return await self.process_dalle_request(text_message, history)
        else:
            history.append(
                ChatCompletionUserMessageParam(
                    role="user",
                    content=[
                        ChatCompletionContentPartTextParam(type="text", text=message.caption or "Посмотри на изображение"),
                        ChatCompletionContentPartImageParam(type="image_url", image_url={"url": url}),
                    ],
                )
            )
            response = await self._client.chat.completions.create(
                model=model,
                messages=history,
            )

            reply = response.choices[0].message.content

            history.append(ChatCompletionAssistantMessageParam(role="assistant", content=reply))

            return GPTMessageResponse(text=reply)

    async def _handle_voice(self, message: Message, history, model: str):
        file = await message.bot.get_file(message.voice.file_id)
        url = f"https://api.telegram.org/file/bot{message.bot.token}/{file.file_path}"
        transcript = await self._transcribe_audio(url)
        if image_prompt := self._parse_image_prompt(transcript):
            logger.info(f"Detected image generation prompt: {image_prompt}")
            text_message = Message(**{**message.model_dump(), "text": image_prompt})
            return await self.process_dalle_request(text_message, history)
        else:
            history.append(ChatCompletionUserMessageParam(role="user", content=transcript))
            response = await self._client.chat.completions.create(
                model=model,
                messages=history,
            )

            reply = response.choices[0].message.content

            history.append(ChatCompletionAssistantMessageParam(role="assistant", content=reply))

            return GPTMessageResponse(text=reply)

    async def _handle_text(self, message: Message, history, model: str):
        if image_prompt := self._parse_image_prompt(message.text):
            logger.info(f"Detected image generation prompt: {image_prompt}")
            text_message = Message(**{**message.model_dump(), "text": image_prompt})
            return await self.process_dalle_request(text_message, history)
        else:
            history.append(ChatCompletionUserMessageParam(role="user", content=message.text))
            response = await self._client.chat.completions.create(
                model=model,
                messages=history,
            )

            reply = response.choices[0].message.content

            history.append(ChatCompletionAssistantMessageParam(role="assistant", content=reply))

            return GPTMessageResponse(text=reply)
