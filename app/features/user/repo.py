from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .model import User
from .schemas import UserCreate, UserUpdate


class UserRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(self) -> list[User]:
        result = await self.session.execute(select(User))

        return list(result.scalars().all())

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def create(self, data: UserCreate) -> User:
        user = User(**data.model_dump())

        self.session.add(user)

        await self.session.commit()
        await self.session.refresh(user)

        return user

    async def update(self, user: User, data: UserUpdate) -> User:
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(user, field, value)

        await self.session.commit()
        await self.session.refresh(user)

        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.commit()
