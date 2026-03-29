from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.validation import MAX_STRING_LENGTH
from app.models import Model


class User(Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), unique=True, nullable=False)
