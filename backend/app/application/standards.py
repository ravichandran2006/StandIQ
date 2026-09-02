from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.errors import ConflictError, NotFoundError
from app.domain.models import Standard
from app.infrastructure.repositories.standards import StandardRepository


class StandardService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = StandardRepository(session)
        self.session = session

    async def create(self, *, is_number: str, title: str, standard_type: str | None, status: str, publication_info: str | None, review_info: str | None, technical_committee: str | None) -> Standard:
        standard = Standard(is_number=is_number, title=title, standard_type=standard_type, status=status, publication_info=publication_info, review_info=review_info, technical_committee=technical_committee)
        try:
            return await self.repository.add(standard)
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("A standard with this IS number already exists") from exc

    async def get(self, standard_id: str) -> Standard:
        standard = await self.repository.get_by_id(standard_id)
        if standard is None:
            raise NotFoundError("Standard not found")
        return standard

    async def list(self, *, offset: int, limit: int, status: str | None, search: str | None) -> tuple[Sequence[Standard], int]:
        return await self.repository.list(offset=offset, limit=limit, status=status, search=search)

    async def update(self, standard_id: str, values: dict[str, object]) -> Standard:
        standard = await self.get(standard_id)
        for field, value in values.items():
            setattr(standard, field, value)
        try:
            await self.session.flush()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("The updated standard conflicts with an existing record") from exc
        await self.session.refresh(standard)
        return standard

    async def delete(self, standard_id: str) -> None:
        standard = await self.get(standard_id)
        await self.repository.delete(standard)

    async def versions(self, standard_id: str):
        await self.get(standard_id)
        return await self.repository.get_versions(standard_id)

    async def relationships(self, standard_id: str):
        await self.get(standard_id)
        return await self.repository.get_relationships(standard_id)