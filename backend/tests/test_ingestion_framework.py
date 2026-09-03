from datetime import datetime, timezone

import pytest
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.models import IngestionRun, Standard, StandardVersion
from app.domain.models.base import Base
from app.ingestion.adapters import SourceAdapter
from app.ingestion.contracts import RawSourceRecord
from app.ingestion.service import IngestionService
from app.ingestion.transform import normalize_is_number, parse_date, parse_standard, validate_standard


class MemoryAdapter(SourceAdapter):
    source_type = "synthetic-test"

    def __init__(self, payloads: list[dict]):
        self.payloads = payloads

    async def records(self, *, incremental: bool = False):
        del incremental
        for index, payload in enumerate(self.payloads):
            yield RawSourceRecord(self.source_type, "https://example.invalid/test", f"fixture-{index}", payload, datetime.now(timezone.utc))


@pytest.fixture
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    @event.listens_for(engine.sync_engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as database_session:
        yield database_session
    await engine.dispose()


def standard_payload(**overrides) -> dict:
    payload = {"is_number": "is 123 : 2024", "title": "  Synthetic   standard ", "status": "Active", "versions": [{"edition_label": "2024 edition", "edition_year": 2024, "publication_date": "2024-02-03", "is_current": True}], "amendments": [{"edition_label": "2024 edition", "amendment_label": "Amd 1", "publication_date": "03/04/2024"}], "classifications": [{"scheme": "TEST", "code": "001", "title": "Synthetic classification"}]}
    payload.update(overrides)
    return payload


def test_normalization_and_parsing() -> None:
    assert normalize_is_number(" is 12: 2024 ") == "IS 12 : 2024"
    assert parse_date("03/04/2024").isoformat() == "2024-04-03"
    record = parse_standard(RawSourceRecord("test", "https://example.invalid", "id", standard_payload(), datetime.now(timezone.utc)))
    assert record.title == "Synthetic standard"
    assert record.versions[0].publication_date.isoformat() == "2024-02-03"
    assert record.amendments_by_edition["2024 edition"][0].amendment_label == "Amd 1"


def test_validation_rejects_missing_and_unsupported_data() -> None:
    raw = RawSourceRecord("test", "https://example.invalid", "id", {"is_number": "", "title": "", "status": "invented"}, datetime.now(timezone.utc))
    errors = validate_standard(parse_standard(raw))
    assert "is_number is required" in errors
    assert "title is required" in errors
    assert "unsupported status: invented" in errors


@pytest.mark.asyncio
async def test_dry_run_does_not_modify_database(session: AsyncSession) -> None:
    stats = await IngestionService(session).ingest(MemoryAdapter([standard_payload()]), dry_run=True)
    assert stats.discovered == 1
    assert stats.inserted == 1
    assert (await session.execute(select(Standard))).scalars().all() == []


@pytest.mark.asyncio
async def test_idempotent_upsert_and_provenance(session: AsyncSession) -> None:
    adapter = MemoryAdapter([standard_payload()])
    first = await IngestionService(session).ingest(adapter)
    second = await IngestionService(session).ingest(adapter)
    assert first.discovered == 1 and first.inserted == 1 and first.failed == 0
    assert second.discovered == 1 and second.skipped >= 2 and second.failed == 0
    assert len((await session.execute(select(Standard))).scalars().all()) == 1
    assert len((await session.execute(select(StandardVersion))).scalars().all()) == 1
    assert len((await session.execute(select(IngestionRun))).scalars().all()) == 2


@pytest.mark.asyncio
async def test_failed_record_is_tracked_without_losing_valid_record(session: AsyncSession) -> None:
    stats = await IngestionService(session).ingest(MemoryAdapter([standard_payload(), standard_payload(title="", is_number="")]))
    assert stats.discovered == 2
    assert stats.inserted == 1
    assert stats.failed == 1
    run = (await session.execute(select(IngestionRun))).scalar_one()
    assert run.records_failed == 1
    assert "is_number is required" in run.error_summary
