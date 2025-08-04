from pydantic import BaseModel


class GPTMessageResponse(BaseModel):
    text: str | None = None
    image_url: str | None = None
