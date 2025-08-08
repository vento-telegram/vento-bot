from datetime import datetime, UTC
from typing import Annotated

from sqlalchemy import MetaData, func
from sqlalchemy.orm import Mapped, mapped_column, declarative_mixin, DeclarativeBase

metadata = MetaData()

@declarative_mixin
class TimeMixin:
    timestamp = Annotated[
        datetime,
        mapped_column(
            nullable=False,
            default=lambda: datetime.now(UTC).replace(tzinfo=None),
            server_default=func.CURRENT_TIMESTAMP(),
        ),
    ]

    created_at: Mapped[timestamp] = mapped_column(server_default=func.now())
    updated_at: Mapped[timestamp] = mapped_column(onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))

class Base(DeclarativeBase):
    metadata = metadata


class UserOrm(Base, TimeMixin):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(nullable=True)
    balance: Mapped[int] = mapped_column(nullable=False, server_default="0")

    def __str__(self):
        return f"{self.telegram_id}"


class PriceOrm(Base, TimeMixin):
    __tablename__ = 'prices'

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(nullable=False, unique=True)
    price: Mapped[int] = mapped_column(nullable=False, server_default="0")


class LedgerOrm(Base, TimeMixin):
    __tablename__ = 'ledger'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(nullable=False)
    delta: Mapped[int] = mapped_column(nullable=False)
    reason: Mapped[str] = mapped_column(nullable=False)
    meta: Mapped[str | None] = mapped_column(nullable=True)
