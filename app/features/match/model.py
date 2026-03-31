import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Model, TimestampMixin


class MatchStatus(str, enum.Enum):
    PENDING = "PENDING"
    VOTING = "VOTING"
    FINISHED = "FINISHED"


if TYPE_CHECKING:
    from app.features.entity.model import Entity
    from app.features.session.model import Session


class Match(Model, TimestampMixin):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    round: Mapped[int]
    position: Mapped[int]
    entity_1_id: Mapped[int | None] = mapped_column(
        ForeignKey("entities.id", ondelete="SET NULL")
    )
    entity_2_id: Mapped[int | None] = mapped_column(
        ForeignKey("entities.id", ondelete="SET NULL")
    )
    is_bye: Mapped[bool] = mapped_column(default=False)
    next_match_id: Mapped[int | None] = mapped_column(
        ForeignKey("matches.id", ondelete="SET NULL")
    )

    winner_entity_id: Mapped[int | None] = mapped_column(
        ForeignKey("entities.id", ondelete="SET NULL")
    )
    status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus), default=MatchStatus.PENDING
    )

    session: Mapped["Session"] = relationship(back_populates="matches")
    entity_1: Mapped["Entity | None"] = relationship(foreign_keys=[entity_1_id])
    entity_2: Mapped["Entity | None"] = relationship(foreign_keys=[entity_2_id])
    winner_entity: Mapped["Entity | None"] = relationship(
        foreign_keys=[winner_entity_id]
    )
    next_match: Mapped["Match | None"] = relationship(
        remote_side=[id], foreign_keys=[next_match_id]
    )
