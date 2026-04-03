from functools import wraps

from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.di.exceptions import ErrAlreadyExists, ErrNotFound
from app.features.user.model import User
from app.di.result import Err, Ok

from .schemas import CreateUserParams, MeRes, UserCredsRes


def catch_database_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except NoResultFound:
            return Err(ErrNotFound())
        except IntegrityError as e:
            # psycopg2 uses .pgcode; psycopg3 uses .sqlstate
            pgcode = getattr(e.orig, "pgcode", None) or getattr(
                e.orig, "sqlstate", None
            )
            if pgcode == "23505":
                return Err(ErrAlreadyExists())
            raise

    return wrapper


class AuthRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @catch_database_errors
    async def create_user(self, params: CreateUserParams):
        result = await self._session.execute(
            insert(User)
            .values(
                email=params.email,
                username=params.username,
                hashed_password=params.hashed_password,
            )
            .returning(User.id)
        )
        await self._session.commit()
        user_id = result.scalar_one()
        return Ok(user_id)

    @catch_database_errors
    async def get_user_by_id(self, user_id: int):
        result = await self._session.execute(
            select(User.id, User.email, User.username).where(User.id == user_id)
        )
        row = result.one()
        return Ok(MeRes(id=row.id, email=row.email, username=row.username))

    @catch_database_errors
    async def get_user_creds(self, email: str):
        result = await self._session.execute(
            select(User.id, User.email, User.username, User.hashed_password).where(User.email == email)
        )
        row = result.one()
        return Ok(
            UserCredsRes(
                id=row.id, email=row.email, username=row.username, hashed_password=row.hashed_password
            )
        )
