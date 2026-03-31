from fastapi import APIRouter

from app.features.auth import router as auth_router
from app.features.entity import api as entity_api
from app.features.healthcheck import api as healthcheck_api
from app.features.session import api as session_api
from app.features.tournament import api as tournament_api
from app.features.user import api

api_router = APIRouter()
api_router.include_router(
    healthcheck_api.router, prefix="/healthcheck", tags=["Healthcheck"]
)
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(api.router, prefix="/users", tags=["Users"])
api_router.include_router(
    tournament_api.router, prefix="/tournaments", tags=["Tournaments"]
)
api_router.include_router(
    entity_api.router, prefix="/tournaments/{tournament_id}/entities", tags=["Entities"]
)
api_router.include_router(
    session_api.tournament_router,
    prefix="/tournaments/{tournament_id}/sessions",
    tags=["Sessions"],
)
api_router.include_router(
    session_api.session_router, prefix="/sessions", tags=["Sessions"]
)
