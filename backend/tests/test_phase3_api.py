from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

from app.domain.models.base import Base
from app.domain.models import Standard, StandardRelationship, StandardVersion
from app.main import create_app
from app.settings import Settings


@pytest.fixture
async def client(tmp_path: Path):
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'api.db'}"
    settings = Settings(_env_file=None, app_env="test", database_url=database_url)
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    app = create_app(settings)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    await engine.dispose()


@pytest.mark.asyncio
async def test_standard_crud_and_pagination(client: AsyncClient) -> None:
    payload = {"is_number": "TEST-API-001", "title": "Synthetic API standard", "status": "test-only"}
    created = await client.post("/api/v1/standards", json=payload)
    assert created.status_code == 201
    standard = created.json()
    assert standard["is_number"] == payload["is_number"]

    listed = await client.get("/api/v1/standards?search=Synthetic&limit=1")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    standard_id = standard["id"]

    updated = await client.patch(f"/api/v1/standards/{standard_id}", json={"title": "Updated synthetic standard"})
    assert updated.status_code == 200
    assert updated.json()["title"] == "Updated synthetic standard"

    fetched = await client.get(f"/api/v1/standards/{standard_id}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == standard_id

    deleted = await client.delete(f"/api/v1/standards/{standard_id}")
    assert deleted.status_code == 204
    assert (await client.get(f"/api/v1/standards/{standard_id}")).status_code == 404


@pytest.mark.asyncio
async def test_validation_not_found_and_duplicate_errors(client: AsyncClient) -> None:
    invalid = await client.post("/api/v1/standards", json={"is_number": "", "title": ""})
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "validation_error"

    missing = await client.get("/api/v1/standards/missing-id")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "not_found"

    payload = {"is_number": "TEST-API-002", "title": "Synthetic duplicate test", "status": "test-only"}
    assert (await client.post("/api/v1/standards", json=payload)).status_code == 201
    duplicate = await client.post("/api/v1/standards", json=payload)
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "conflict"


@pytest.mark.asyncio
async def test_related_resource_endpoints(client: AsyncClient) -> None:
    database = client._transport.app.state.database
    async for session in database.session():
        source = Standard(is_number="TEST-API-003", title="Source fixture", status="test-only")
        target = Standard(is_number="TEST-API-004", title="Target fixture", status="test-only")
        source.versions.append(StandardVersion(edition_label="Synthetic edition", edition_year=2026, status="test-only"))
        source.relationships_from.append(StandardRelationship(target_standard=target, relationship_type="RELATED", evidence_note="Synthetic fixture only"))
        session.add(source)
        await session.commit()
        source_id = source.id

    versions = await client.get(f"/api/v1/standards/{source_id}/versions")
    relationships = await client.get(f"/api/v1/standards/{source_id}/relationships")
    assert versions.status_code == 200
    assert versions.json()[0]["edition_label"] == "Synthetic edition"
    assert relationships.status_code == 200
    assert relationships.json()[0]["relationship_type"] == "RELATED"