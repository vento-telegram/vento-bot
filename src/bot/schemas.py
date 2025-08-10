from datetime import datetime

from pydantic import BaseModel, Field


class GPTMessageResponse(BaseModel):
    text: str | None = None
    image_url: str | None = None
    video_url: str | None = None


class RequestsCounts(BaseModel):
    gpt_5: int = Field(0, alias="gpt-5")
    gpt_5_mini: int = Field(0, alias="gpt-5-mini")
    dalle3: int = 0


class UserTotals(BaseModel):
    total_spent: int
    today_spent: int
    requests: RequestsCounts
    last_request_at: datetime | None = None
