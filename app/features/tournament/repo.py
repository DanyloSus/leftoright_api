from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .model import Tournament
from .schemas import TournamentCreate, TournamentUpdate


class TournamentRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all_by_user(self, user_id: int) -> list[Tournament]:
        result = await self.session.execute(
            select(Tournament).where(Tournament.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_by_id(self, tournament_id: int) -> Tournament | None:
        return await self.session.get(Tournament, tournament_id)

    async def create(self, user_id: int, data: TournamentCreate) -> Tournament:
        tournament = Tournament(**data.model_dump(), user_id=user_id)

        self.session.add(tournament)

        await self.session.commit()
        await self.session.refresh(tournament)

        return tournament

    async def update(
        self, tournament: Tournament, data: TournamentUpdate
    ) -> Tournament:
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(tournament, field, value)

        await self.session.commit()
        await self.session.refresh(tournament)

        return tournament

    async def delete(self, tournament: Tournament) -> None:
        await self.session.delete(tournament)
        await self.session.commit()
