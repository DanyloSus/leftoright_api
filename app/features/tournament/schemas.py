from pydantic import BaseModel, Field

from app.constants.validation import MAX_STRING_LENGTH


class TournamentCreate(BaseModel):
    name: str = Field(..., max_length=MAX_STRING_LENGTH)
    description: str | None = Field(None, max_length=MAX_STRING_LENGTH)


class TournamentUpdate(BaseModel):
    name: str | None = Field(None, max_length=MAX_STRING_LENGTH)
    description: str | None = Field(None, max_length=MAX_STRING_LENGTH)


class TournamentRead(BaseModel):
    id: int
    name: str
    description: str | None
    user_id: int

    model_config = {"from_attributes": True}
