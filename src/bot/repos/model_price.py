from sqlalchemy import select

from bot.database.models import PriceOrm
from bot.entities.model_price import PriceEntity
from bot.interfaces.repos.base import DataMapper
from bot.interfaces.repos.model_price import AbcPriceRepo
from bot.repos.base import BaseRepo


class PriceDataMapper(DataMapper):
    def model_to_entity(self, instance: PriceOrm) -> PriceEntity:
        return PriceEntity.model_validate(instance, from_attributes=True)


class PriceRepo(AbcPriceRepo, BaseRepo):
    _mapper_class = PriceDataMapper

    async def get_by_key(self, key: str) -> PriceEntity | None:
        stmt = select(PriceOrm).filter_by(key=key).limit(1)
        instance = await self.session.scalar(stmt)
        return self.map_model_to_entity(instance) if instance else None
