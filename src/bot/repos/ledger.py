from sqlalchemy import insert, select

from bot.database.models import LedgerOrm
from bot.entities.ledger import LedgerEntity
from bot.interfaces.repos.base import DataMapper
from bot.interfaces.repos.ledger import AbcLedgerRepo
from bot.repos.base import BaseRepo


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

    async def list_for_user(self, user_id: int, limit: int = 20) -> list[LedgerEntity]:
        stmt = select(LedgerOrm).where(LedgerOrm.user_id == user_id).order_by(LedgerOrm.id.desc()).limit(limit)
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [self.map_model_to_entity(r) for r in rows]


