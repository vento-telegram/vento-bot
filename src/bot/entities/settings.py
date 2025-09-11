from datetime import datetime, UTC

from pydantic import BaseModel, Field


class SettingsDTO(BaseModel):
    id: int | None = None
    key: str | None = None
    value: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at: datetime | None = None


class SettingsEntity(SettingsDTO):
    pass
