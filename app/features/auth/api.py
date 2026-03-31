from fastapi import APIRouter

from app.di.auth import UserIdDep

from .di import AuthServiceDep
from .schemas import LoginWithEmailReq, MeRes, RegisterWithEmailReq, TokenPairSchema

router = APIRouter()


@router.get("/me", response_model=MeRes)
async def get_me(user_id: UserIdDep, service: AuthServiceDep):
    res, err = await service.get_me(user_id=user_id)
    if err:
        raise err
    return res


@router.post("/register", response_model=TokenPairSchema)
async def register(service: AuthServiceDep, req: RegisterWithEmailReq):
    res, err = await service.register_with_email_provider(req=req)
    if err:
        raise err
    return res


@router.post("/login", response_model=TokenPairSchema)
async def login(service: AuthServiceDep, req: LoginWithEmailReq):
    res, err = await service.login_user_with_email_provider(req=req)
    if err:
        raise err
    return res
