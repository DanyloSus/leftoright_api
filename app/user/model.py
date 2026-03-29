from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from shared.constants.validation import MAX_STRING_LENGTH
from shared.models import Model


class User(Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), unique=True, nullable=False)
