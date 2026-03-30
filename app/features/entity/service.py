from fastapi import HTTPException, status

from app.features.tournament.repo import TournamentRepo

from .repo import EntityRepo
from .schemas import EntityCreate, EntityRead


class EntityService:
    def __init__(self, repo: EntityRepo, tournament_repo: TournamentRepo) -> None:
        self.repo = repo
        self.tournament_repo = tournament_repo

    async def _get_tournament_or_fail(self, tournament_id: int, user_id: int):
        tournament = await self.tournament_repo.get_by_id(tournament_id)

        if not tournament:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")

        return tournament

    async def get_all(self, tournament_id: int, user_id: int) -> list[EntityRead]:
        await self._get_tournament_or_fail(tournament_id, user_id)

        entities = await self.repo.get_all_by_tournament(tournament_id)

        return [EntityRead.model_validate(e) for e in entities]

    async def create(self, tournament_id: int, user_id: int, data: EntityCreate) -> EntityRead:
        tournament = await self._get_tournament_or_fail(tournament_id, user_id)

        if tournament.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        entity = await self.repo.create(tournament_id, data)

        return EntityRead.model_validate(entity)

    async def delete(self, tournament_id: int, entity_id: int, user_id: int) -> None:
        tournament = await self._get_tournament_or_fail(tournament_id, user_id)

        if tournament.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        entity = await self.repo.get_by_id(entity_id)

        if not entity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")

        if entity.tournament_id != tournament_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")

        await self.repo.delete(entity)
