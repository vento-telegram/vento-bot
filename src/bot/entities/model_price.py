from datetime import datetime, UTC

from pydantic import BaseModel, Field


class PriceDTO(BaseModel):
    id: int | None = None
    key: str | None = None
    price: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at: datetime | None = None


class PriceEntity(PriceDTO):
    pass
