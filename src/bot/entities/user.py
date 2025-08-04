from datetime import datetime, UTC

from pydantic import BaseModel, Field


class UserDTO(BaseModel):
    id: int | None = None
    telegram_id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))


class UserEntity(UserDTO):
    pass
