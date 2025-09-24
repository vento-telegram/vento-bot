from sqlalchemy import select

from bot.database.models import SettingsOrm
from bot.entities.settings import SettingsEntity
from bot.interfaces.repos.base import DataMapper
from bot.interfaces.repos.settings import AbcSettingsRepo
from bot.repos.base import BaseRepo


class SettingsDataMapper(DataMapper):
    def model_to_entity(self, instance: SettingsOrm) -> SettingsEntity:
        return SettingsEntity.model_validate(instance, from_attributes=True)


class SettingsRepo(AbcSettingsRepo, BaseRepo):
    _mapper_class = SettingsDataMapper

    async def get_by_key(self, key: str) -> SettingsEntity | None:
        stmt = select(SettingsOrm).filter_by(key=key).limit(1)
        instance = await self.session.scalar(stmt)
        return self.map_model_to_entity(instance) if instance else None
