from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.di.auth import UserIdDep
from app.features.entity.repo import EntityRepo
from app.features.match.repo import MatchRepo
from app.features.match.service import MatchService
from app.features.tournament.repo import TournamentRepo
from configs.session import get_session

from .repo import SessionRepo
from .schemas import SessionRead, VoteRequest, VoteResponse
from .service import SessionService
from .ws import session_websocket

tournament_router = APIRouter()
session_router = APIRouter()
session_router.add_api_websocket_route("/{session_id}/ws", session_websocket)


def get_service(session: AsyncSession = Depends(get_session)) -> SessionService:
    return SessionService(
        session_repo=SessionRepo(session),
        match_service=MatchService(MatchRepo(session)),
        entity_repo=EntityRepo(session),
        tournament_repo=TournamentRepo(session),
    )


@tournament_router.post("/", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
async def start_session(
    tournament_id: int,
    user_id: UserIdDep,
    service: SessionService = Depends(get_service),
):
    return await service.start_session(tournament_id, user_id)


@session_router.get("/{session_id}", response_model=SessionRead)
async def get_session_state(
    session_id: int,
    service: SessionService = Depends(get_service),
):
    return await service.get_session(session_id)


@session_router.post("/{session_id}/vote", response_model=VoteResponse)
async def vote(
    session_id: int,
    data: VoteRequest,
    user_id: UserIdDep,
    service: SessionService = Depends(get_service),
):
    return await service.vote(session_id, user_id, data.chosen_entity_id)
