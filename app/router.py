from fastapi import APIRouter
from app.features.user import api
                                   
api_router = APIRouter()                                      
api_router.include_router(api.router, prefix="/users", tags=["Users"])    
