from fastapi import APIRouter

from app.features.auth import router as auth_router
from app.features.tournament import api as tournament_api
from app.features.user import api

api_router = APIRouter()
api_router.include_router(auth_router, prefix='/auth', tags=['Authentication'])
api_router.include_router(api.router, prefix='/users', tags=['Users'])
api_router.include_router(tournament_api.router, prefix='/tournaments', tags=['Tournaments'])
