from pydantic import BaseModel, Field

from app.constants.validation import MAX_STRING_LENGTH


class UserCreate(BaseModel):
    email: str = Field(..., max_length=MAX_STRING_LENGTH)
    username: str = Field(..., max_length=MAX_STRING_LENGTH)


class UserUpdate(BaseModel):
    email: str | None = Field(None, max_length=MAX_STRING_LENGTH)
    username: str | None = Field(None, max_length=MAX_STRING_LENGTH)


class UserRead(BaseModel):
    id: int
    email: str
    username: str

    model_config = {"from_attributes": True}
