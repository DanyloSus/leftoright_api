from pydantic import BaseModel, EmailStr, Field


class RegisterWithEmailReq(BaseModel):
    email: EmailStr
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=10, max_length=100)


class LoginWithEmailReq(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=100)


class TokenPairSchema(BaseModel):
    access_token: str
    refresh_token: str


class UserRes(BaseModel):
    id: int
    email: str

    model_config = {'from_attributes': True}


class UserCredsRes(BaseModel):
    id: int
    email: str
    hashed_password: str | None

    model_config = {'from_attributes': True}


class MeRes(BaseModel):
    id: int
    email: str
    username: str

    model_config = {'from_attributes': True}


class CreateUserParams(BaseModel):
    email: str
    username: str
    hashed_password: str | None = None
