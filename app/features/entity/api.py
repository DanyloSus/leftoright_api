from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.di.auth import UserIdDep
from app.features.tournament.repo import TournamentRepo
from configs.session import get_session

from .repo import EntityRepo
from .schemas import EntityCreate, EntityRead
from .service import EntityService

router = APIRouter()


def get_service(session: AsyncSession = Depends(get_session)) -> EntityService:
    return EntityService(EntityRepo(session), TournamentRepo(session))


@router.get("/", response_model=list[EntityRead])
async def list_entities(
    tournament_id: int,
    user_id: UserIdDep,
    service: EntityService = Depends(get_service),
):
    return await service.get_all(tournament_id, user_id)


@router.post("/", response_model=EntityRead, status_code=status.HTTP_201_CREATED)
async def create_entity(
    tournament_id: int,
    data: EntityCreate,
    user_id: UserIdDep,
    service: EntityService = Depends(get_service),
):
    return await service.create(tournament_id, user_id, data)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity(
    tournament_id: int,
    entity_id: int,
    user_id: UserIdDep,
    service: EntityService = Depends(get_service),
):
    await service.delete(tournament_id, entity_id, user_id)
