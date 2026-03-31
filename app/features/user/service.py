from fastapi import HTTPException, status

from .repo import UserRepo
from .schemas import UserCreate, UserRead, UserUpdate


class UserService:
    def __init__(self, repo: UserRepo) -> None:
        self.repo = repo

    async def get_all(self) -> list[UserRead]:
        users = await self.repo.get_all()

        return [UserRead.model_validate(u) for u in users]

    async def get_by_id(self, user_id: int) -> UserRead:
        user = await self.repo.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return UserRead.model_validate(user)

    async def create(self, data: UserCreate) -> UserRead:
        user = await self.repo.create(data)

        return UserRead.model_validate(user)

    async def update(self, user_id: int, data: UserUpdate) -> UserRead:
        user = await self.repo.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        user = await self.repo.update(user, data)

        return UserRead.model_validate(user)

    async def delete(self, user_id: int) -> None:
        user = await self.repo.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        await self.repo.delete(user)
