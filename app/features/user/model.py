from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Model, TimestampMixin

if TYPE_CHECKING:
    from app.features.tournament.model import Tournament


class User(Model, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str | None]

    tournaments: Mapped[list["Tournament"]] = relationship(back_populates="user")
