from fastapi import HTTPException, status

from .repo import TournamentRepo
from .schemas import TournamentCreate, TournamentRead, TournamentUpdate


class TournamentService:
    def __init__(self, repo: TournamentRepo) -> None:
        self.repo = repo

    async def get_all(self, user_id: int) -> list[TournamentRead]:
        tournaments = await self.repo.get_all_by_user(user_id)

        return [TournamentRead.model_validate(t) for t in tournaments]

    async def get_by_id(self, tournament_id: int, user_id: int) -> TournamentRead:
        tournament = await self.repo.get_by_id(tournament_id)

        if not tournament:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found"
            )

        return TournamentRead.model_validate(tournament)

    async def create(self, user_id: int, data: TournamentCreate) -> TournamentRead:
        tournament = await self.repo.create(user_id, data)

        return TournamentRead.model_validate(tournament)

    async def update(
        self, tournament_id: int, user_id: int, data: TournamentUpdate
    ) -> TournamentRead:
        tournament = await self.repo.get_by_id(tournament_id)

        if not tournament:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found"
            )

        if tournament.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        tournament = await self.repo.update(tournament, data)

        return TournamentRead.model_validate(tournament)

    async def delete(self, tournament_id: int, user_id: int) -> None:
        tournament = await self.repo.get_by_id(tournament_id)

        if not tournament:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found"
            )

        if tournament.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        await self.repo.delete(tournament)
