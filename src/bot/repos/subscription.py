from datetime import UTC, datetime

from sqlalchemy import select, update, func

from bot.database.models import SubscriptionOrm
from bot.entities.subscription import SubscriptionEntity
from bot.interfaces.repos.base import DataMapper
from bot.interfaces.repos.subscription import AbcSubscriptionRepo
from bot.repos.base import BaseRepo


class SubscriptionDataMapper(DataMapper):
    def model_to_entity(self, instance: SubscriptionOrm) -> SubscriptionEntity:
        return SubscriptionEntity.model_validate(instance, from_attributes=True)


class SubscriptionRepo(AbcSubscriptionRepo, BaseRepo):
    _mapper_class = SubscriptionDataMapper

    async def get_active_by_user_id(self, user_id: int) -> SubscriptionEntity | None:
        stmt = (
            select(SubscriptionOrm)
            .where(SubscriptionOrm.user_id == user_id)
            .where(SubscriptionOrm.till >= datetime.now(UTC).replace(tzinfo=None))
            .order_by(SubscriptionOrm.till.desc())
            .limit(1)
        )
        inst = await self.session.scalar(stmt)
        return self.map_model_to_entity(inst) if inst else None

    async def get_latest_by_user_id(self, user_id: int) -> SubscriptionEntity | None:
        stmt = (
            select(SubscriptionOrm)
            .where(SubscriptionOrm.user_id == user_id)
            .order_by(SubscriptionOrm.till.desc())
            .limit(1)
        )
        inst = await self.session.scalar(stmt)
        return self.map_model_to_entity(inst) if inst else None

    async def create(self, user_id: int, till) -> SubscriptionEntity:
        sub = SubscriptionOrm(user_id=user_id, till=till, requests_count=0, mini_requests_count=0)
        self.session.add(sub)
        await self.session.flush()
        await self.session.refresh(sub)
        return self.map_model_to_entity(sub)

    async def update_counts(self, sub_id: int, requests_count: int | None, mini_requests_count: int | None) -> SubscriptionEntity | None:
        values = {}
        if requests_count is not None:
            values['requests_count'] = requests_count
        if mini_requests_count is not None:
            values['mini_requests_count'] = mini_requests_count
        if not values:
            return await self._get_by_id(sub_id)
        # Touch updated_at on counters update
        values['updated_at'] = func.now()
        stmt = (
            update(SubscriptionOrm)
            .where(SubscriptionOrm.id == sub_id)
            .values(**values)
            .returning(SubscriptionOrm)
        )
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        return self.map_model_to_entity(model) if model else None

    async def update_till(self, sub_id: int, till) -> SubscriptionEntity | None:
        stmt = (
            update(SubscriptionOrm)
            .where(SubscriptionOrm.id == sub_id)
            .values(till=till)
            .returning(SubscriptionOrm)
        )
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        return self.map_model_to_entity(model) if model else None

    async def _get_by_id(self, sub_id: int) -> SubscriptionEntity | None:
        stmt = select(SubscriptionOrm).where(SubscriptionOrm.id == sub_id).limit(1)
        model = await self.session.scalar(stmt)
        return self.map_model_to_entity(model) if model else None
