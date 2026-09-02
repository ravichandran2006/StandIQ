from datetime import datetime, timezone

import pytest
from sqlalchemy import event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.models import (
    Amendment,
    Classification,
    IngestionRun,
    SourceRecord,
    Standard,
    StandardClassification,
    StandardRelationship,
    StandardVersion,
)
from app.domain.models.base import Base
from app.infrastructure.repositories.standards import StandardRepository


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


@pytest.mark.asyncio
async def test_repository_and_version_amendment_relationships(session: AsyncSession) -> None:
    source = SourceRecord(source_type="synthetic-test", external_identifier="fixture-1", source_status="test-only")
    standard = Standard(is_number="TEST-001", title="Synthetic test standard", status="test-only", source_record=source)
    version = StandardVersion(edition_label="Synthetic edition", edition_year=2026, standard=standard, status="test-only")
    amendment = Amendment(amendment_label="Test amendment 1", standard_version=version, details="Synthetic fixture only")
    session.add_all([source, standard, version, amendment])
    await session.commit()

    repository = StandardRepository(session)
    found = await repository.get_by_is_number("TEST-001")

    assert found is standard
    assert found.versions[0].amendments[0].amendment_label == "Test amendment 1"
    assert found.source_record.external_identifier == "fixture-1"


@pytest.mark.asyncio
async def test_unique_source_standard_and_version_constraints(session: AsyncSession) -> None:
    session.add(SourceRecord(source_type="synthetic-test", external_identifier="duplicate"))
    await session.commit()
    session.add(SourceRecord(source_type="synthetic-test", external_identifier="duplicate"))
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()

    standard = Standard(is_number="TEST-002", title="Synthetic test standard", status="test-only")
    session.add(standard)
    await session.commit()
    standard_id = standard.id
    session.add(Standard(is_number="TEST-002", title="Duplicate synthetic standard", status="test-only"))
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()

    session.add(StandardVersion(standard_id=standard_id, edition_label="Edition", edition_year=2026, status="test-only"))
    await session.commit()
    session.add(StandardVersion(standard_id=standard_id, edition_label="Duplicate edition", edition_year=2026, status="test-only"))
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()


@pytest.mark.asyncio
async def test_classification_and_relationship_integrity(session: AsyncSession) -> None:
    first = Standard(is_number="TEST-003", title="First synthetic standard", status="test-only")
    second = Standard(is_number="TEST-004", title="Second synthetic standard", status="test-only")
    classification = Classification(scheme="TEST", code="001", title="Synthetic classification")
    session.add_all([first, second, classification])
    await session.commit()

    session.add(StandardClassification(standard_id=first.id, classification_id=classification.id))
    session.add(StandardRelationship(source_standard_id=first.id, target_standard_id=second.id, relationship_type="RELATED"))
    await session.commit()
    assert (await session.execute(select(StandardRelationship))).scalar_one().relationship_type == "RELATED"

    session.add(StandardRelationship(source_standard_id=first.id, target_standard_id=first.id, relationship_type="RELATED"))
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()


@pytest.mark.asyncio
async def test_ingestion_run_tracks_source_provenance(session: AsyncSession) -> None:
    started = datetime.now(timezone.utc)
    run = IngestionRun(source_name="synthetic-test", started_at=started, status="completed", records_discovered=1, records_inserted=1)
    source = SourceRecord(source_type="synthetic-test", external_identifier="fixture-run", ingestion_run=run, source_status="test-only")
    session.add(source)
    await session.commit()

    loaded = await session.get(IngestionRun, run.id)
    assert loaded.records_inserted == 1
    assert loaded.source_records[0].external_identifier == "fixture-run"
