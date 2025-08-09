from sqlalchemy import insert, select, update, func, case, ColumnElement

from bot.database.models import LedgerOrm
from bot.entities.ledger import LedgerEntity
from bot.enums import LedgerReasonEnum
from bot.interfaces.repos.base import DataMapper
from bot.interfaces.repos.ledger import AbcLedgerRepo
from bot.repos.base import BaseRepo
from bot.schemas import RequestsCounts, UserTotals


class LedgerDataMapper(DataMapper):
    def model_to_entity(self, instance: LedgerOrm) -> LedgerEntity:
        return LedgerEntity.model_validate(instance, from_attributes=True)


class LedgerRepo(AbcLedgerRepo, BaseRepo):
    _mapper_class = LedgerDataMapper

    async def add(self, entry: LedgerEntity) -> LedgerEntity:
        stmt = insert(LedgerOrm).values(**entry.model_dump(exclude_none=True)).returning(LedgerOrm)
        result = await self.session.execute(stmt)
        row = result.scalar_one()
        return self.map_model_to_entity(row)

    async def update_meta_by_id(self, ledger_id: int, meta: str) -> LedgerEntity | None:
        stmt = (
            update(LedgerOrm)
            .where(LedgerOrm.id == ledger_id)
            .values(meta=meta)
            .returning(LedgerOrm)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        return self.map_model_to_entity(row) if row else None

    async def total_spent_today(self) -> int:
        return await self._sum_negative_delta(func.date(LedgerOrm.created_at) == self._today())

    async def requests_count_today(self) -> int:
        stmt = select(func.count()).where(
            LedgerOrm.delta < 0,
            func.date(LedgerOrm.created_at) == self._today(),
        )
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    async def requests_by_model_today(self) -> RequestsCounts:
        today = self._today()
        stmt = select(
            self._model_case(LedgerReasonEnum.gpt5_request).label("gpt-5"),
            self._model_case(LedgerReasonEnum.gpt5_mini_request).label("gpt-5-mini"),
            self._model_case(LedgerReasonEnum.dalle3_image).label("dalle3"),
        ).where(
            LedgerOrm.delta < 0,
            func.date(LedgerOrm.created_at) == today,
        )
        result = await self.session.execute(stmt)
        row = result.one()
        m = row._mapping
        return RequestsCounts(**{
            "gpt-5": int(m.get("gpt-5") or 0),
            "gpt-5-mini": int(m.get("gpt-5-mini") or 0),
            "dalle3": int(m.get("dalle3") or 0),
        })

    async def user_totals(self, user_id: int) -> UserTotals:
        total_spent = await self._sum_negative_delta(LedgerOrm.user_id == user_id)
        today_spent = await self._sum_negative_delta(
            LedgerOrm.user_id == user_id,
            func.date(LedgerOrm.created_at) == self._today()
        )
        model_stmt = select(
            self._model_case(LedgerReasonEnum.gpt5_request).label("gpt-5"),
            self._model_case(LedgerReasonEnum.gpt5_mini_request).label("gpt-5-mini"),
            self._model_case(LedgerReasonEnum.dalle3_image).label("dalle3"),
            func.max(LedgerOrm.created_at).label("last_request_at"),
        ).where(
            LedgerOrm.user_id == user_id,
            LedgerOrm.delta < 0,
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
                "dalle3": int(m.get("dalle3") or 0),
            }),
            last_request_at=m.get("last_request_at"),
        )

    def _model_case(self, reason_enum_value: str) -> ColumnElement:
        return func.sum(
            case(
                (LedgerOrm.reason.ilike(f'%{reason_enum_value}%'), 1),
                else_=0
            )
        )

    def _today(self):
        return func.date(func.now())

    async def _sum_negative_delta(self, *where) -> int:
        stmt = select(func.coalesce(func.sum(-LedgerOrm.delta), 0)).where(LedgerOrm.delta < 0, *where)
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)
