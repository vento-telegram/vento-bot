import logging

from aiogram.types import Message
from openai import OpenAI as OpenAIClient

from bot.interfaces.services.gpt import AbcOpenAIService
from bot.interfaces.uow import AbcUnitOfWork

logger = logging.getLogger(__name__)

class OpenAIService(AbcOpenAIService):
    def __init__(self, uow: AbcUnitOfWork, client: OpenAIClient):
        self._uow = uow
        self._client = client

    async def process_message(self, message: Message) -> str:
        response = await self._client.responses.create(
            model="gpt-4o",
            input=message.text,
        )
        return response.output_text
