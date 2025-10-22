from sqlalchemy import ColumnElement, case, func, insert, select, update

from bot.database.models import TransactionOrm
from bot.entities.transaction import TransactionEntity
from bot.enums import TransactionReasonEnum
from bot.interfaces.repos.base import DataMapper
from bot.interfaces.repos.transaction import AbcTransactionRepo
from bot.repos.base import BaseRepo
from bot.schemas import RequestsCounts, UserTotals
from datetime import date as _date, datetime, time as _time, timedelta, timezone
from zoneinfo import ZoneInfo


class TransactionDataMapper(DataMapper):
    def model_to_entity(self, instance: TransactionOrm) -> TransactionEntity:
        return TransactionEntity.model_validate(instance, from_attributes=True)


class TransactionRepo(AbcTransactionRepo, BaseRepo):
    _mapper_class = TransactionDataMapper

    _MSK = ZoneInfo("Europe/Moscow")

    async def add(self, entry: TransactionEntity) -> TransactionEntity:
        stmt = insert(TransactionOrm).values(**entry.model_dump(exclude_none=True)).returning(TransactionOrm)
        result = await self.session.execute(stmt)
        row = result.scalar_one()
        return self.map_model_to_entity(row)

    async def update_meta_by_id(self, transaction_id: int, meta: str) -> TransactionEntity | None:
        stmt = (
            update(TransactionOrm)
            .where(TransactionOrm.id == transaction_id)
            .values(meta=meta)
            .returning(TransactionOrm)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        return self.map_model_to_entity(row) if row else None

    async def total_spent_today(self) -> int:
        return await self._sum_negative_delta(func.date(TransactionOrm.created_at) == self._today())

    async def requests_count_today(self) -> int:
        stmt = select(func.count()).where(
            TransactionOrm.delta < 0,
            func.date(TransactionOrm.created_at) == self._today(),
        )
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    async def requests_by_model_today(self) -> RequestsCounts:
        today = self._today()
        stmt = select(
            self._model_case(TransactionReasonEnum.gpt_request).label("gpt-5"),
            self._model_case(TransactionReasonEnum.gpt_mini_request).label("gpt-5-mini"),
        ).where(
            TransactionOrm.delta < 0,
            func.date(TransactionOrm.created_at) == today,
        )
        result = await self.session.execute(stmt)
        row = result.one()
        m = row._mapping
        return RequestsCounts(**{
            "gpt-5": int(m.get("gpt-5") or 0),
            "gpt-5-mini": int(m.get("gpt-5-mini") or 0),
        })


    async def count_active_users_today(self) -> int:
        start_utc, end_utc = self._msk_day_bounds()
        stmt = select(func.count(func.distinct(TransactionOrm.user_id))).where(
            TransactionOrm.delta < 0,
            TransactionOrm.created_at >= start_utc,
            TransactionOrm.created_at < end_utc,
        )
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)


    async def user_totals(self, user_id: int) -> UserTotals:
        total_spent = await self._sum_negative_delta(TransactionOrm.user_id == user_id)
        today_spent = await self._sum_negative_delta(
            TransactionOrm.user_id == user_id,
            func.date(TransactionOrm.created_at) == self._today()
        )
        model_stmt = select(
            self._model_case(TransactionReasonEnum.gpt_request).label("gpt-5"),
            self._model_case(TransactionReasonEnum.gpt_mini_request).label("gpt-5-mini"),
            func.max(TransactionOrm.created_at).label("last_request_at"),
        ).where(
            TransactionOrm.user_id == user_id,
            TransactionOrm.delta < 0,
        )
        model_result = await self.session.execute(model_stmt)
        row = model_result.one()
        m = row._mapping
        return UserTotals(
            total_spent=total_spent,
            today_spent=today_spent,
            requests=RequestsCounts(**{
                "gpt-5": int(m.get("gpt-5") or 0),
                "gpt-5-mini": int(m.get("gpt-5-mini") or 0),
            }),
            last_request_at=m.get("last_request_at"),
        )

    async def list_today_by_reasons(self, reasons: list[str]) -> list[TransactionEntity]:
        start_utc, end_utc = self._msk_day_bounds()
        stmt = select(TransactionOrm).where(
            TransactionOrm.created_at >= start_utc,
            TransactionOrm.created_at < end_utc,
            TransactionOrm.reason.in_(reasons),
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [self.map_model_to_entity(r) for r in rows]

    async def list_by_date_by_reasons(self, day: _date, reasons: list[str]) -> list[TransactionEntity]:
        start_utc, end_utc = self._msk_day_bounds(day)
        stmt = select(TransactionOrm).where(
            TransactionOrm.created_at >= start_utc,
            TransactionOrm.created_at < end_utc,
            TransactionOrm.reason.in_(reasons),
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [self.map_model_to_entity(r) for r in rows]

    def _model_case(self, reason_enum_value: str) -> ColumnElement:
        return func.sum(
            case(
                (TransactionOrm.reason.ilike(f'%{reason_enum_value}%'), 1),
                else_=0
            )
        )

    def _today(self):
        return func.date(func.now())

    async def _sum_negative_delta(self, *where) -> int:
        stmt = select(func.coalesce(func.sum(-TransactionOrm.delta), 0)).where(TransactionOrm.delta < 0, *where)
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    def _msk_day_bounds(self, day: _date | None = None) -> tuple[datetime, datetime]:
        if day is None:
            now_msk = datetime.now(self._MSK)
            day = now_msk.date()
        start_msk = datetime.combine(day, _time(0, 0), tzinfo=self._MSK)
        end_msk = start_msk + timedelta(days=1)
        start_utc = start_msk.astimezone(timezone.utc).replace(tzinfo=None)
        end_utc = end_msk.astimezone(timezone.utc).replace(tzinfo=None)
        return start_utc, end_utc
