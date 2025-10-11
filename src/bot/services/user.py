import logging
from typing import Tuple

from aiogram.types import User as TelegramUser

from bot.entities.transaction import TransactionEntity
from bot.entities.user import UserDTO, UserEntity
from bot.enums import TransactionReasonEnum
from bot.interfaces.services.settings import AbcSettingsService
from bot.interfaces.services.user import AbcUserService
from bot.interfaces.uow import AbcUnitOfWork

logger = logging.getLogger(__name__)

class UserService(AbcUserService):
    def __init__(self, uow: AbcUnitOfWork, settings_service: AbcSettingsService):
        self._uow = uow
        self._settings_service = settings_service

    async def is_user_new(self, telegram_user: TelegramUser, ref_from: str | None = None) -> Tuple[UserEntity, bool]:
        user_data = UserDTO(telegram_id=telegram_user.id, username=telegram_user.username, from_=ref_from)
        start_bonus = await self._settings_service.get_value("start_bonus")
        async with self._uow:
            user, is_new = await self._uow.user.get_or_create(user_data)

            if is_new:
                logger.info(f"New user registered: {user.telegram_id}")
                updated = await self._update_balance(user.id, int(start_bonus), TransactionReasonEnum.welcome_bonus)
                user = updated if updated else user

        return user, is_new

    async def _update_balance(self, user_id: int, delta: int, reason: TransactionReasonEnum) -> UserEntity | None:
        updated = await self._uow.user.update_balance_by_user_id(user_id, delta)
        if updated:
            await self._uow.transaction.add(TransactionEntity(user_id=user_id,
                                                         delta=delta,
                                                         reason=reason,
                                                         ),
                                       )
        return updated


    async def get_user(self, telegram_id: int) -> UserEntity | None:
        async with self._uow:
            user = await self._uow.user.get_by_telegram_id(telegram_id)
        return user

    async def add_tokens_by_username(self, username: str, amount: int, reason: TransactionReasonEnum) -> UserEntity | None:
        async with self._uow:
            user = await self._uow.user.get_by_username(username)
            if not user:
                return None
            return await self._update_balance(user.id, amount, reason)

    async def add_tokens_by_telegram_id(self, telegram_id: int, amount: int, reason: TransactionReasonEnum) -> UserEntity | None:
        async with self._uow:
            user = await self._uow.user.get_by_telegram_id(telegram_id)
            if not user:
                return None
            return await self._update_balance(user.id, amount, reason)

    async def block_user_by_username(self, username: str) -> UserEntity | None:
        async with self._uow:
            return await self._uow.user.set_blocked_by_username(username, True)

    async def unblock_user_by_username(self, username: str) -> UserEntity | None:
        async with self._uow:
            return await self._uow.user.set_blocked_by_username(username, False)

    async def daily_min_balance_topup(self, min_balance: int) -> int:
        updated_count = 0
        async with self._uow:
            users = await self._uow.user.list_with_balance_lt(min_balance)
            for u in users:
                delta = int(min_balance) - int(u.balance)
                if delta <= 0:
                    continue
                updated = await self._update_balance(u.id, delta, TransactionReasonEnum.daily_bonus)
                if updated:
                    updated_count += 1
        return updated_count
