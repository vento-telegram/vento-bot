import logging
from typing import Tuple

from bot.entities.user import UserDTO, UserEntity
from bot.enums import LedgerReasonEnum
from bot.interfaces.services.user import AbcUserService
from bot.interfaces.uow import AbcUnitOfWork
from aiogram.types import User as TelegramUser
from bot.entities.ledger import LedgerEntity
from bot.settings import settings

logger = logging.getLogger(__name__)

class UserService(AbcUserService):
    def __init__(self, uow: AbcUnitOfWork):
        self._uow = uow

    async def is_user_new(self, telegram_user: TelegramUser) -> Tuple[UserEntity, bool]:
        user_data = UserDTO(telegram_id=telegram_user.id, username=telegram_user.username)
        async with self._uow:
            user, is_new = await self._uow.user.get_or_create(user_data)

            if is_new:
                logger.info(f"New user registered: {user.telegram_id}")
                updated = await self._update_balance(user.id, settings.WELCOME_BONUS_AMOUNT, LedgerReasonEnum.welcome_bonus)
                user = updated if updated else user

        return user, is_new

    async def _update_balance(self, user_id: int, delta: int, reason: LedgerReasonEnum) -> UserEntity | None:
        updated = await self._uow.user.update_balance_by_user_id(user_id, delta)
        if updated:
            await self._uow.ledger.add(LedgerEntity(user_id=user_id,
                    delta=delta,
                    reason=reason,
                ),
            )
        return updated


    async def get_user(self, telegram_id: int) -> UserEntity | None:
        async with self._uow:
            user = await self._uow.user.get_by_telegram_id(telegram_id)
        return user

    async def add_tokens_by_username(self, username: str, amount: int, reason: LedgerReasonEnum) -> UserEntity | None:
        async with self._uow:
            user = await self._uow.user.get_by_username(username)
            if not user:
                return None
            return await self._update_balance(user.id, amount, reason)

    async def block_user_by_username(self, username: str) -> UserEntity | None:
        async with self._uow:
            return await self._uow.user.set_blocked_by_username(username, True)

    async def unblock_user_by_username(self, username: str) -> UserEntity | None:
        async with self._uow:
            return await self._uow.user.set_blocked_by_username(username, False)
