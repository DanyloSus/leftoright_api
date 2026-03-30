from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .model import Match


class MatchRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_bulk(self, matches: list[Match]) -> list[Match]:
        self.session.add_all(matches)
        await self.session.flush()
        return matches

    async def get_by_session_round_position(
        self, session_id: int, round: int, position: int
    ) -> Match | None:
        result = await self.session.execute(
            select(Match)
            .where(
                Match.session_id == session_id,
                Match.round == round,
                Match.position == position,
            )
        )
        return result.scalar_one_or_none()
