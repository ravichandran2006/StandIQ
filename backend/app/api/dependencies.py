from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.standards import StandardService
from app.application.errors import DatabaseUnavailableError


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    database = request.app.state.database
    if not database.configured:
        raise DatabaseUnavailableError("Database is not configured")
    async for session in database.session():
        yield session


def get_standard_service(session: AsyncSession = Depends(get_session)) -> StandardService:
    return StandardService(session)