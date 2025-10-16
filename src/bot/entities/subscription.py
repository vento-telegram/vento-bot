from datetime import UTC, datetime

from pydantic import BaseModel, Field


class SubscriptionDTO(BaseModel):
    id: int | None = None
    user_id: int
    till: datetime
    requests_count: int = 0
    mini_requests_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at: datetime | None = None


class SubscriptionEntity(SubscriptionDTO):
    pass

