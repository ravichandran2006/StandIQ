import pytest
from sqlalchemy import event, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.application.recommendations import RecommendationService
from app.domain.models import Amendment, Certification, Classification, QcoRecord, SourceRecord, Standard, StandardRelationship
from app.domain.models.base import Base
from app.infrastructure.vector import InMemoryVectorIndex, PineconeVectorIndex
from app.ingestion.adapters import BisMetadataAdapter
from app.ingestion.service import IngestionService
from app.settings import Settings


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
async def test_bis_metadata_adapter_records():
    adapter = BisMetadataAdapter(max_records=5)
    records = []
    async for record in adapter.records():
        records.append(record)
    assert len(records) > 0
    first = records[0]
    assert first.source_type == "BIS"
    assert first.source_url.startswith("https://www.bis.gov.in/")
    assert first.external_identifier.startswith("IS ")
    assert "title" in first.payload
    assert "status" in first.payload


@pytest.mark.asyncio
async def test_bis_metadata_ingestion_into_database(session: AsyncSession):
    adapter = BisMetadataAdapter(max_records=100)
    service = IngestionService(session)
    stats = await service.ingest(adapter, mode="full")

    assert stats.discovered > 0
    assert stats.inserted > 0
    assert stats.failed == 0

    # Verify PostgreSQL system of record
    standards_count = int((await session.execute(select(func.count()).select_from(Standard))).scalar_one())
    assert standards_count > 0

    # Verify provenance
    provenance_count = int((await session.execute(select(func.count()).select_from(SourceRecord))).scalar_one())
    assert provenance_count > 0

    # Verify relations and classifications
    relationships_count = int((await session.execute(select(func.count()).select_from(StandardRelationship))).scalar_one())
    assert relationships_count >= 0

    classifications_count = int((await session.execute(select(func.count()).select_from(Classification))).scalar_one())
    assert classifications_count > 0


@pytest.mark.asyncio
async def test_recommendation_service_with_bis_standards(session: AsyncSession):
    # Perform initial ingestion of BIS standards
    adapter = BisMetadataAdapter(max_records=100)
    service = IngestionService(session)
    await service.ingest(adapter, mode="full")


    rec_service = RecommendationService(session)
    result = await rec_service.recommend("Steel bars for concrete reinforcement structural code", language="en")

    assert result.summary["standards_in_database"] > 0
    assert result.summary["status"] in {"recommendations_found", "live_source_used"}
    assert len(result.standards) > 0

    top_recommendation = result.standards[0]
    assert "is_number" in top_recommendation
    assert top_recommendation["is_number"].startswith("IS ")
    assert top_recommendation["evidence_state"] in {"supported", "requires_verification"}
    assert "version" in top_recommendation
    assert "compliance" in top_recommendation



@pytest.mark.asyncio
async def test_in_memory_and_pinecone_vector_index():
    idx = InMemoryVectorIndex()
    vec1 = [0.1] * 1024
    vec2 = [0.9] * 1024
    await idx.upsert([
        {"id": "std-1", "values": vec1, "metadata": {"is_number": "IS 800"}},
        {"id": "std-2", "values": vec2, "metadata": {"is_number": "IS 456"}},
    ])

    matches = await idx.query(vec1, top_k=2)
    assert len(matches) == 2
    assert matches[0].vector_id == "std-1"

    settings = Settings()
    pinecone_idx = PineconeVectorIndex(settings)
    assert await pinecone_idx.check() in {"healthy", "configured", "not_configured"}
