from datetime import UTC, datetime
from typing import Annotated

from sqlalchemy import BigInteger, Boolean, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declarative_mixin, mapped_column

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
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(nullable=True)
    balance: Mapped[int] = mapped_column(nullable=False, server_default="0")
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    def __str__(self):
        return f"{self.telegram_id}"


class SettingsOrm(Base, TimeMixin):
    __tablename__ = 'settings'

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(nullable=False, unique=True)
    value: Mapped[str] = mapped_column(nullable=False, server_default="0")


class TransactionOrm(Base, TimeMixin):
    __tablename__ = 'transaction'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(nullable=False)
    delta: Mapped[int] = mapped_column(nullable=False)
    reason: Mapped[str] = mapped_column(nullable=False)
    meta: Mapped[str | None] = mapped_column(nullable=True)
