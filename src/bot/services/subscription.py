from __future__ import annotations

from datetime import UTC, datetime, timedelta

from bot.entities.subscription import SubscriptionEntity
from bot.entities.transaction import TransactionEntity
from bot.enums import TransactionReasonEnum, BotModeEnum
from bot.interfaces.services.settings import AbcSettingsService
from bot.interfaces.services.subscription import AbcSubscriptionService
from bot.interfaces.uow import AbcUnitOfWork


class SubscriptionService(AbcSubscriptionService):
    def __init__(self, uow: AbcUnitOfWork, settings_service: AbcSettingsService):
        self._uow = uow
        self._settings = settings_service

    async def get_active_by_user_id(self, user_id: int) -> SubscriptionEntity | None:
        async with self._uow:
            return await self._uow.subscription.get_active_by_user_id(user_id)

    async def activate_or_extend_for_telegram(self, telegram_id: int, days: int, bonus_tokens: int) -> SubscriptionEntity | None:
        now = datetime.now(UTC).replace(tzinfo=None)
        async with self._uow:
            user = await self._uow.user.get_by_telegram_id(telegram_id)
            if not user:
                return None
            current = await self._uow.subscription.get_latest_by_user_id(user.id)
            if current and current.till and current.till > now:
                new_till = current.till + timedelta(days=days)
                updated = await self._uow.subscription.update_till(current.id, new_till)
                sub = updated if updated else current
            else:
                new_till = now + timedelta(days=days)
                sub = await self._uow.subscription.create(user.id, new_till)

            # credit bonus tokens
            await self._uow.user.update_balance_by_user_id(user.id, bonus_tokens)
            await self._uow.transaction.add(
                TransactionEntity(user_id=user.id, delta=bonus_tokens, reason=TransactionReasonEnum.purchase_subscription_bonus)
            )
            return sub

    async def mark_and_check_limit(self, user_id: int, mode: str) -> bool:
        # mode is BotModeEnum.gpt or BotModeEnum.gpt_mini string value
        now = datetime.now(UTC).replace(tzinfo=None)
        async with self._uow:
            sub = await self._uow.subscription.get_active_by_user_id(user_id)
            if not sub:
                return False

            # Reset daily counters when day changes based on updated_at date
            try:
                last = sub.updated_at or sub.created_at
            except Exception:
                last = sub.created_at
            last_day = (last.date() if last else now.date())
            today = now.date()
            if last_day != today:
                sub = await self._uow.subscription.update_counts(sub.id, 0, 0) or sub

            # Get limits from settings (0 or missing -> unlimited)
            raw_gpt = await self._settings.get_value("sub_gpt_daily_limit")
            raw_mini = await self._settings.get_value("sub_gpt_mini_daily_limit")
            try:
                lim_gpt = int(raw_gpt) if raw_gpt is not None else 0
            except Exception:
                lim_gpt = 0
            try:
                lim_mini = int(raw_mini) if raw_mini is not None else 0
            except Exception:
                lim_mini = 0

            if mode == BotModeEnum.gpt:
                if lim_gpt > 0 and sub.requests_count >= lim_gpt:
                    return False
                await self._uow.subscription.update_counts(sub.id, sub.requests_count + 1, None)
                return True
            elif mode == BotModeEnum.gpt_mini:
                if lim_mini > 0 and sub.mini_requests_count >= lim_mini:
                    return False
                await self._uow.subscription.update_counts(sub.id, None, sub.mini_requests_count + 1)
                return True
            else:
                return False

