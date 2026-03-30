from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .model import Entity
from .schemas import EntityCreate


class EntityRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all_by_tournament(self, tournament_id: int) -> list[Entity]:
        result = await self.session.execute(
            select(Entity).where(Entity.tournament_id == tournament_id)
        )
        return list(result.scalars().all())

    async def get_by_id(self, entity_id: int) -> Entity | None:
        return await self.session.get(Entity, entity_id)

    async def create(self, tournament_id: int, data: EntityCreate) -> Entity:
        entity = Entity(**data.model_dump(), tournament_id=tournament_id)

        self.session.add(entity)

        await self.session.commit()
        await self.session.refresh(entity)

        return entity

    async def delete(self, entity: Entity) -> None:
        await self.session.delete(entity)
        await self.session.commit()
