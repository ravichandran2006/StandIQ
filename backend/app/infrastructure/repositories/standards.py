from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Standard


class StandardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, standard_id: str) -> Standard | None:
        return await self.session.get(Standard, standard_id)

    async def get_by_is_number(self, is_number: str) -> Standard | None:
        result = await self.session.execute(select(Standard).where(Standard.is_number == is_number))
        return result.scalar_one_or_none()

    async def list_by_status(self, status: str) -> Sequence[Standard]:
        result = await self.session.execute(select(Standard).where(Standard.status == status).order_by(Standard.is_number))
        return result.scalars().all()

    async def add(self, standard: Standard) -> Standard:
        self.session.add(standard)
        await self.session.flush()
        return standard