from datetime import timedelta

import structlog

from configs.jwt import JWTConfig
from app.auth.context import context
from app.auth.token import create_jwt_token
from app.di.exceptions import ErrPermissionDenied
from app.di.result import Err, Ok

from .repo import AuthRepo
from .schemas import (
    CreateUserParams,
    LoginWithEmailReq,
    RegisterWithEmailReq,
    TokenPairSchema,
    UserRes,
)

logger = structlog.get_logger(__name__)


class AuthService:
    def __init__(self, repo: AuthRepo, jwt_config: JWTConfig) -> None:
        self._repo = repo
        self._jwt_config = jwt_config

    async def get_me(self, user_id: int):
        user, err = await self._repo.get_user_by_id(user_id)
        if err:
            return Err(err)
        return Ok(user)

    async def register_with_email_provider(self, req: RegisterWithEmailReq):
        logger.info("register_attempt", email=req.email, username=req.username)
        hashed_password = context.hash(req.password)
        user_id, err = await self._repo.create_user(
            CreateUserParams(
                email=req.email, username=req.username, hashed_password=hashed_password
            )
        )
        if err:
            logger.warning("register_failed", email=req.email, reason=str(err))
            return Err(err)
        logger.info("register_success", email=req.email, user_id=user_id)
        user = UserRes(id=user_id, email=req.email, username=req.username)
        tokens = self.__create_token_pair(user_id, user)
        return Ok(tokens)

    async def login_user_with_email_provider(self, req: LoginWithEmailReq):
        logger.info("login_attempt", email=req.email)
        user_creds, err = await self._repo.get_user_creds(req.email)
        if err:
            logger.warning("login_failed", email=req.email, reason="user_not_found")
            return Err(err)
        if not context.verify(req.password, user_creds.hashed_password):
            logger.warning(
                "login_failed", email=req.email, reason="invalid_credentials"
            )
            return Err(ErrPermissionDenied("Invalid credentials"))
        logger.info("login_success", email=req.email, user_id=user_creds.id)
        user = UserRes(id=user_creds.id, email=user_creds.email, username=user_creds.username)
        tokens = self.__create_token_pair(user_creds.id, user)
        return Ok(tokens)

    def __create_token_pair(self, user_id: int, user: UserRes) -> TokenPairSchema:
        access_token = create_jwt_token(
            secret_key=self._jwt_config.SECRET_KEY,
            algorithm=self._jwt_config.ALGORITHM,
            data={"sub": str(user_id)},
            expires=timedelta(minutes=self._jwt_config.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh_token = create_jwt_token(
            secret_key=self._jwt_config.SECRET_KEY,
            algorithm=self._jwt_config.ALGORITHM,
            data={"sub": str(user_id)},
            expires=timedelta(minutes=self._jwt_config.REFRESH_TOKEN_EXPIRE_MINUTES),
        )
        return TokenPairSchema(access_token=access_token, refresh_token=refresh_token, user=user)
