from sqlalchemy.ext.asyncio import AsyncSession

from .model import Match


class MatchRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_bulk(self, matches: list[Match]) -> list[Match]:
        self.session.add_all(matches)
        await self.session.flush()
        return matches
