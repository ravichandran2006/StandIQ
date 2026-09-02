from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import Standard, StandardRelationship, StandardVersion


class StandardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, standard_id: str) -> Standard | None:
        statement = (
            select(Standard)
            .options(selectinload(Standard.versions), selectinload(Standard.relationships_from), selectinload(Standard.relationships_to))
            .where(Standard.id == standard_id)
        )
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def get_by_is_number(self, is_number: str) -> Standard | None:
        result = await self.session.execute(select(Standard).where(Standard.is_number == is_number))
        return result.scalar_one_or_none()

    async def list(self, *, offset: int, limit: int, status: str | None = None, search: str | None = None) -> tuple[Sequence[Standard], int]:
        filters = []
        if status:
            filters.append(Standard.status == status)
        if search:
            filters.append(Standard.title.ilike(f"%{search}%"))
        statement = select(Standard).where(*filters).order_by(Standard.is_number).offset(offset).limit(limit)
        count_statement = select(func.count()).select_from(Standard).where(*filters)
        rows = (await self.session.execute(statement)).scalars().all()
        total = (await self.session.execute(count_statement)).scalar_one()
        return rows, total

    async def list_by_status(self, status: str) -> Sequence[Standard]:
        rows, _ = await self.list(offset=0, limit=100, status=status)
        return rows

    async def add(self, standard: Standard) -> Standard:
        self.session.add(standard)
        await self.session.flush()
        return standard

    async def get_versions(self, standard_id: str) -> Sequence[StandardVersion]:
        result = await self.session.execute(select(StandardVersion).where(StandardVersion.standard_id == standard_id).order_by(StandardVersion.edition_year.desc().nullslast(), StandardVersion.edition_label))
        return result.scalars().all()

    async def get_relationships(self, standard_id: str) -> Sequence[StandardRelationship]:
        statement = (
            select(StandardRelationship)
            .options(selectinload(StandardRelationship.target_standard), selectinload(StandardRelationship.source_standard))
            .where((StandardRelationship.source_standard_id == standard_id) | (StandardRelationship.target_standard_id == standard_id))
            .order_by(StandardRelationship.relationship_type, StandardRelationship.created_at)
        )
        return (await self.session.execute(statement)).scalars().all()

    async def delete(self, standard: Standard) -> None:
        await self.session.delete(standard)
        await self.session.flush()