from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Model, TimestampMixin


class User(Model, TimestampMixin):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str | None]
