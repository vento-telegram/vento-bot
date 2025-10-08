from datetime import UTC, datetime

from pydantic import BaseModel, Field


class TransactionDTO(BaseModel):
    id: int | None = None
    user_id: int
    delta: int
    reason: str
    meta: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at: datetime | None = None


class TransactionEntity(TransactionDTO):
    pass
