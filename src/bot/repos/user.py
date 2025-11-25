from sqlalchemy import insert, select, update, func

from bot.database.models import UserOrm
from bot.entities.user import UserDTO, UserEntity
from bot.interfaces.repos.base import DataMapper
from bot.interfaces.repos.user import AbcUserRepo
from datetime import date as _date, datetime, time as _time, timedelta, timezone
from zoneinfo import ZoneInfo

from bot.repos.base import BaseRepo


class UserDataMapper(DataMapper):
    def model_to_entity(self, instance: UserOrm) -> UserEntity:
        return UserEntity.model_validate(instance, from_attributes=True)


class UserRepo(AbcUserRepo, BaseRepo):
    _mapper_class = UserDataMapper

    _MSK = ZoneInfo("Europe/Moscow")

    def _msk_day_bounds(self, day: _date | None = None) -> tuple[datetime, datetime]:
        if day is None:
            now_msk = datetime.now(self._MSK)
            day = now_msk.date()
        start_msk = datetime.combine(day, _time(0, 0), tzinfo=self._MSK)
        end_msk = start_msk + timedelta(days=1)
        start_utc = start_msk.astimezone(timezone.utc).replace(tzinfo=None)
        end_utc = end_msk.astimezone(timezone.utc).replace(tzinfo=None)
        return start_utc, end_utc

    async def get_or_create(self, user_data: UserDTO) -> tuple[UserEntity, bool]:
        stmt = select(UserOrm).filter_by(telegram_id=user_data.telegram_id).limit(1)
        user = await self.session.scalar(stmt)
        if user:
            return self.map_model_to_entity(user), False

        stmt = insert(UserOrm).values(**user_data.model_dump(exclude_none=True)).returning(UserOrm)
        result = await self.session.execute(stmt)
        user = result.scalar_one()
        return self.map_model_to_entity(user), True

    async def get_by_telegram_id(self, telegram_id: int) -> UserEntity | None:
        stmt = select(UserOrm).filter_by(telegram_id=telegram_id).limit(1)
        user = await self.session.scalar(stmt)
        return self.map_model_to_entity(user) if user else None

    async def update_balance_by_user_id(self, user_id: int, delta: int) -> UserEntity | None:
        stmt = (
            update(UserOrm)
            .where(UserOrm.id == user_id)
            .values(balance=UserOrm.balance + delta)
            .returning(UserOrm)
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        return self.map_model_to_entity(user) if user else None

    async def get_by_username(self, username: str) -> UserEntity | None:
        stmt = select(UserOrm).filter_by(username=username).limit(1)
        user = await self.session.scalar(stmt)
        return self.map_model_to_entity(user) if user else None

    async def set_blocked_by_username(self, username: str, is_blocked: bool) -> UserEntity | None:
        stmt = (
            update(UserOrm)
            .where(UserOrm.username == username)
            .values(is_blocked=is_blocked)
            .returning(UserOrm)
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        return self.map_model_to_entity(user) if user else None

    async def get_by_id(self, user_id: int) -> UserEntity | None:
        stmt = select(UserOrm).filter_by(id=user_id).limit(1)
        user = await self.session.scalar(stmt)
        return self.map_model_to_entity(user) if user else None

    async def list_with_balance_lt(self, threshold: int) -> list[UserEntity]:
        stmt = select(UserOrm).where(UserOrm.balance < threshold)
        res = await self.session.scalars(stmt)
        models = list(res.all())
        return [self.map_model_to_entity(m) for m in models]

    async def try_debit(self, user_id: int, amount: int) -> UserEntity | None:
        # Only debit if balance is sufficient to avoid negatives (single SQL atomic check)
        stmt = (
            update(UserOrm)
            .where(UserOrm.id == user_id)
            .where(UserOrm.balance >= amount)
            .values(balance=UserOrm.balance - amount)
            .returning(UserOrm)
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        return self.map_model_to_entity(user) if user else None

    async def list_admins(self) -> list[UserEntity]:
        stmt = select(UserOrm).where(UserOrm.is_admin.is_(True))
        res = await self.session.scalars(stmt)
        models = list(res.all())
        return [self.map_model_to_entity(m) for m in models]

    async def count_all(self) -> int:
        stmt = select(func.count()).select_from(UserOrm)
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    async def count_by_date(self, day: _date) -> int:
        start_utc, end_utc = self._msk_day_bounds(day)
        stmt = select(func.count()).where(
            UserOrm.created_at >= start_utc,
            UserOrm.created_at < end_utc,
        )
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    async def count_today(self) -> int:
        start_utc, end_utc = self._msk_day_bounds()
        stmt = select(func.count()).where(
            UserOrm.created_at >= start_utc,
            UserOrm.created_at < end_utc,
        )
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    async def list_telegram_ids(self) -> list[int]:
        stmt = select(UserOrm.telegram_id).order_by(UserOrm.id)
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [int(tid) for tid in rows if tid is not None]