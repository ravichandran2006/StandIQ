from collections.abc import AsyncGenerator

from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.settings import Settings


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Database:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None
        if settings.database_configured():
            database_url = settings.database_url.get_secret_value()
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
            self.engine = create_async_engine(
                database_url,
                pool_pre_ping=True,
            )
            self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    @property
    def configured(self) -> bool:
        return self.engine is not None

    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        if self.session_factory is None:
            raise RuntimeError("Database is not configured")
        async with self.session_factory() as session:
            yield session

    async def check(self) -> str:
        if self.engine is None:
            return "not_configured"
        try:
            async with self.engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except Exception:
            return "unavailable"
        return "healthy"

    async def close(self) -> None:
        if self.engine is not None:
            await self.engine.dispose()
