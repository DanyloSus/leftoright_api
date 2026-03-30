from pydantic import BaseModel, Field

from app.constants.validation import MAX_STRING_LENGTH


class EntityCreate(BaseModel):
    name: str = Field(..., max_length=MAX_STRING_LENGTH)
    youtube_url: str | None = Field(None, max_length=512)


class EntityRead(BaseModel):
    id: int
    name: str
    youtube_url: str | None
    tournament_id: int

    model_config = {"from_attributes": True}
