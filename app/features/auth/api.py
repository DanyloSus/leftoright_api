from fastapi import APIRouter

from .di import AuthServiceDep
from .schemas import LoginWithEmailReq, RegisterWithEmailReq, TokenPairSchema

router = APIRouter()


@router.post('/register', response_model=TokenPairSchema)
async def register(service: AuthServiceDep, req: RegisterWithEmailReq):
    res, err = await service.register_with_email_provider(req=req)
    if err:
        raise err
    return res


@router.post('/login', response_model=TokenPairSchema)
async def login(service: AuthServiceDep, req: LoginWithEmailReq):
    res, err = await service.login_user_with_email_provider(req=req)
    if err:
        raise err
    return res
