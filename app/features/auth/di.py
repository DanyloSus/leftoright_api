from typing import Annotated

from fastapi import Depends

from configs.jwt import JWTConfigDep
from configs.session import AsyncSessionDep

from .repo import AuthRepo
from .service import AuthService


def __get_repo(session: AsyncSessionDep) -> AuthRepo:
    return AuthRepo(session)


def __get_service(
    jwt_config: JWTConfigDep,
    repo: AuthRepo = Depends(__get_repo),
) -> AuthService:
    return AuthService(repo, jwt_config)


AuthServiceDep = Annotated[AuthService, Depends(__get_service)]
