from sqlalchemy import select, insert, update

from bot.database.models import UserOrm
from bot.entities.user import UserEntity, UserDTO
from bot.interfaces.repos.base import DataMapper
from bot.interfaces.repos.user import AbcUserRepo
from bot.repos.base import BaseRepo


class UserDataMapper(DataMapper):
    def model_to_entity(self, instance: UserOrm) -> UserEntity:
        return UserEntity.model_validate(instance, from_attributes=True)


class UserRepo(AbcUserRepo, BaseRepo):
    _mapper_class = UserDataMapper

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