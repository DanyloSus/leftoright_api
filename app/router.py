from fastapi import APIRouter

from app.features.auth import router as auth_router
from app.features.user import api

api_router = APIRouter()
api_router.include_router(auth_router, prefix='/auth', tags=['Authentication'])
api_router.include_router(api.router, prefix='/users', tags=['Users'])
