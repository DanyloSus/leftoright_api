from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Model, TimestampMixin

if TYPE_CHECKING:
    from app.features.tournament.model import Tournament


class Entity(Model, TimestampMixin):
    __tablename__ = 'entities'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    youtube_url: Mapped[str | None] = mapped_column(String(512))
    tournament_id: Mapped[int] = mapped_column(
        ForeignKey('tournaments.id', ondelete='CASCADE'), index=True
    )

    tournament: Mapped["Tournament"] = relationship(back_populates="entities")
