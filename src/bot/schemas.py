from datetime import datetime

from pydantic import BaseModel, Field


class GPTMessageResponse(BaseModel):
    text: str


class RequestsCounts(BaseModel):
    gpt_5: int = Field(0, alias="gpt-5")
    gpt_5_mini: int = Field(0, alias="gpt-5-mini")
    gpt_image: int = Field(0, alias="gpt-image")
    nano_banana: int = Field(0, alias="nano-banana")
    suno: int = Field(0, alias="suno")
    veo: int = Field(0, alias="veo")


class UserTotals(BaseModel):
    total_spent: int
    today_spent: int
    requests: RequestsCounts
    last_request_at: datetime | None = None
    tokens_purchased: int = 0
