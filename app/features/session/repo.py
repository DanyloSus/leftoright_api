from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.match.model import Match

from .model import Session


class SessionRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    async def create(self, **kwargs) -> Session:
        db_session = Session(**kwargs)

        self.db.add(db_session)

        await self.db.flush()
        await self.db.refresh(db_session)

        return db_session

    async def get_by_id(self, session_id: int) -> Session | None:
        result = await self.db.execute(
            select(Session)
            .where(Session.id == session_id)
            .options(
                selectinload(Session.matches).selectinload(Match.entity_1),
                selectinload(Session.matches).selectinload(Match.entity_2),
            )
        )
        return result.scalar_one_or_none()

    async def commit(self) -> None:
        await self.db.commit()


class MatchRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    async def create_bulk(self, matches: list[Match]) -> list[Match]:
        self.db.add_all(matches)
        await self.db.flush()
        return matches

    async def get_by_session_round_position(
        self, session_id: int, round: int, position: int
    ) -> Match | None:
        result = await self.db.execute(
            select(Match)
            .where(
                Match.session_id == session_id,
                Match.round == round,
                Match.position == position,
            )
        )
        return result.scalar_one_or_none()
