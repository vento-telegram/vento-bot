import logging
import re

from aiohttp import ClientSession
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from openai import OpenAI as OpenAIClient
from openai.types import ImagesResponse

from bot.interfaces.services.gpt import AbcOpenAIService
from bot.interfaces.uow import AbcUnitOfWork
from openai.types.chat import (
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam, ChatCompletionMessageParam, ChatCompletionContentPartTextParam,
    ChatCompletionContentPartImageParam, ChatCompletionContentPartInputAudioParam,
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

def extract_image_prompt(text: str) -> str | None:
    if any(kw in text.lower() for kw in IMAGE_EXCLUDE_KEYWORDS):
        return None

    for pattern in IMAGE_PROMPT_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            return next((g for g in groups if g), None)
    return None

logger = logging.getLogger(__name__)

class OpenAIService(AbcOpenAIService):
    def __init__(self, uow: AbcUnitOfWork, client: OpenAIClient):
        self._uow = uow
        self._client = client

    async def process_message(self, message: Message, state: FSMContext) -> GPTMessageResponse:
        text = message.text or ""
        prompt = extract_image_prompt(text)
        if prompt:
            logger.info(f"Detected image generation prompt: {prompt}")
            return GPTMessageResponse(
                image_url=await self._generate_image(prompt)
            )

        data = await state.get_data()
        history: list[ChatCompletionMessageParam] = data.get("history", [])

        if message.photo:
            photo = message.photo[-1]
            file = await message.bot.get_file(photo.file_id)
            url = f"https://api.telegram.org/file/bot{message.bot.token}/{file.file_path}"

            history.append(
                ChatCompletionUserMessageParam(
                    role="user",
                    content=[
                        ChatCompletionContentPartTextParam(type="text", text=message.caption or "Посмотри на изображение"),
                        ChatCompletionContentPartImageParam(type="image_url", image_url={"url": url}),
                    ],
                )
            )

        elif message.voice:
            file = await message.bot.get_file(message.voice.file_id)
            url = f"https://api.telegram.org/file/bot{message.bot.token}/{file.file_path}"
            transcript = await self._transcribe_audio(url)

            history.append(ChatCompletionUserMessageParam(role="user", content=transcript))

        else:
            history.append(ChatCompletionUserMessageParam(role="user", content=message.text))

        response = await self._client.chat.completions.create(
            model="gpt-4o",
            messages=history,
        )

        reply = response.choices[0].message.content

        history.append(ChatCompletionAssistantMessageParam(role="assistant", content=reply))
        await state.update_data(history=history[-10:])

        return GPTMessageResponse(text=reply)

    async def _transcribe_audio(self, url: str) -> str:
        async with ClientSession() as session:
            async with session.get(url) as resp:
                audio_bytes = await resp.read()

        transcript = await self._client.audio.transcriptions.create(
            model="whisper-1",
            file=("voice.ogg", audio_bytes, "audio/ogg")
        )
        return transcript.text

    async def _generate_image(self, prompt: str) -> str:
        try:
            response = await self._client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                response_format="url",
                n=1,
            )
            return response.data[0].url
        except Exception as e:
            logger.exception("Ошибка генерации изображения: %s", e)
            return "❌ Не удалось сгенерировать изображение."
