import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Model, TimestampMixin

if TYPE_CHECKING:
    from app.features.entity.model import Entity
    from app.features.match.model import Match
    from app.features.tournament.model import Tournament
    from app.features.user.model import User


class SessionStatus(str, enum.Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    FINISHED = "finished"
    COMPLETED = "completed"  # kept for backward compat


class Session(Model, TimestampMixin):
    __tablename__ = 'sessions'

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(
        ForeignKey('tournaments.id', ondelete='CASCADE'), index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey('users.id', ondelete='SET NULL'), index=True
    )
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), default=SessionStatus.IN_PROGRESS
    )
    total_rounds: Mapped[int]
    current_round: Mapped[int]
    current_match_position: Mapped[int]
    winner_entity_id: Mapped[int | None] = mapped_column(
        ForeignKey('entities.id', ondelete='SET NULL')
    )

    tournament: Mapped["Tournament"] = relationship()
    user: Mapped["User | None"] = relationship()
    winner_entity: Mapped["Entity | None"] = relationship()
    matches: Mapped[list["Match"]] = relationship(
        back_populates="session", order_by="Match.round, Match.position"
    )
