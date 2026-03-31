from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.di.auth import UserIdDep
from configs.session import get_session

from .repo import TournamentRepo
from .schemas import TournamentCreate, TournamentRead, TournamentUpdate
from .service import TournamentService

router = APIRouter()


def get_service(session: AsyncSession = Depends(get_session)) -> TournamentService:
    return TournamentService(TournamentRepo(session))


@router.get("/", response_model=list[TournamentRead])
async def list_tournaments(
    user_id: UserIdDep, service: TournamentService = Depends(get_service)
):
    return await service.get_all(user_id)


@router.get("/{tournament_id}", response_model=TournamentRead)
async def get_tournament(
    tournament_id: int,
    user_id: UserIdDep,
    service: TournamentService = Depends(get_service),
):
    return await service.get_by_id(tournament_id, user_id)


@router.post("/", response_model=TournamentRead, status_code=status.HTTP_201_CREATED)
async def create_tournament(
    data: TournamentCreate,
    user_id: UserIdDep,
    service: TournamentService = Depends(get_service),
):
    return await service.create(user_id, data)


@router.patch("/{tournament_id}", response_model=TournamentRead)
async def update_tournament(
    tournament_id: int,
    data: TournamentUpdate,
    user_id: UserIdDep,
    service: TournamentService = Depends(get_service),
):
    return await service.update(tournament_id, user_id, data)


@router.delete("/{tournament_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tournament(
    tournament_id: int,
    user_id: UserIdDep,
    service: TournamentService = Depends(get_service),
):
    await service.delete(tournament_id, user_id)
