from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

from app.application.language_labels import language_display_name
from app.application.recommendations import _terms
from app.domain.models.base import Base
from app.domain.models import Certification, QcoMapping, QcoRecord, SourceRecord, Standard, StandardRelationship, StandardVersion
from app.main import create_app
from app.settings import Settings


@pytest.fixture
async def client(tmp_path: Path):
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'features.db'}"
    settings = Settings(_env_file=None, app_env="test", database_url=database_url)
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    app = create_app(settings)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    await engine.dispose()


async def seed_structural_steel(client: AsyncClient) -> tuple[str, str]:
    database = client._transport.app.state.database
    async for session in database.session():
        source = SourceRecord(
            source_type="bis",
            external_identifier="is-2062",
            source_url="https://www.bis.gov.in/know-your-standard/?is_number=IS+2062",
            source_status="retrieved",
        )
        standard = Standard(
            is_number="IS 2062 : 2011",
            title="Hot Rolled Medium and High Tensile Structural Steel - Specification",
            status="current",
            source_record=source,
        )
        standard.versions.append(StandardVersion(edition_label="Seventh Revision", edition_year=2011, is_current=True, status="current"))
        target = Standard(is_number="IS 800 : 2007", title="General Construction In Steel - Code of Practice", status="current")
        standard.relationships_from.append(
            StandardRelationship(
                target_standard=target,
                relationship_type="NORMATIVE",
                evidence_note="Referenced for structural steel design.",
                source_record=source,
            )
        )
        qco = QcoRecord(notification_number="QCO-STEEL-2020", title="Steel Quality Control Order", source_record=source)
        session.add(standard)
        session.add(qco)
        await session.flush()
        session.add(QcoMapping(qco_record=qco, standard=standard, applicability_note="Mandatory for structural steel"))
        session.add(
            Certification(
                scheme_name="ISI Mark Scheme",
                external_identifier="CM/L-1234567",
                title="Mandatory ISI Certification for Structural Steel Bars and Plates",
                applicability_note="Recorded during ingestion",
                source_record=source,
            )
        )
        await session.commit()
        return standard.id, standard.is_number


@pytest.mark.asyncio
async def test_language_display_labels() -> None:
    assert language_display_name("hi") == "हिन्दी"
    assert language_display_name("ta") == "தமிழ்"
    assert language_display_name("ml") == "മലയാളം"
    assert language_display_name("en") == "English"


@pytest.mark.asyncio
async def test_multilingual_requirements_share_canonical_terms() -> None:
    english = "hot rolled medium and high tensile structural steel"
    hindi = "हॉट रोल्ड मीडियम और हाई टेन्साइल स्ट्रक्चरल स्टील"
    english_terms = _terms(english)
    hindi_terms = _terms(hindi)
    assert english_terms == hindi_terms


@pytest.mark.asyncio
async def test_recommendation_returns_language_label_and_mapping(client: AsyncClient) -> None:
    await seed_structural_steel(client)
    response = await client.post(
        "/api/v1/recommendations",
        json={"text": "hot rolled medium and high tensile structural steel"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["requirement"]["detected_language_label"] == "English"
    assert body["standards"]
    assert body["standards"][0]["mapping"]
    assert body["summary"]["canonical_query"]


@pytest.mark.asyncio
async def test_multilingual_recommendations_converge(client: AsyncClient) -> None:
    _, is_number = await seed_structural_steel(client)
    english = await client.post("/api/v1/recommendations", json={"text": "hot rolled medium and high tensile structural steel"})
    hindi = await client.post("/api/v1/recommendations", json={"text": "हॉट रोल्ड मीडियम और हाई टेन्साइल स्ट्रक्चरल स्टील"})
    assert english.status_code == 200 and hindi.status_code == 200
    english_body = english.json()
    hindi_body = hindi.json()
    assert english_body["summary"]["canonical_query"] == hindi_body["summary"]["canonical_query"]
    assert english_body["standards"][0]["is_number"] == hindi_body["standards"][0]["is_number"] == is_number
    assert english_body["standards"][0]["relevance_score"] == hindi_body["standards"][0]["relevance_score"]
    assert language_display_name("hi") not in {"Hi", "HI", "hi", "Hindi"}
    assert hindi_body["requirement"]["detected_language"] == "hi"
    assert hindi_body["requirement"]["detected_language_label"] == "हिन्दी"
    assert english_body["requirement"]["detected_language_label"] == "English"


@pytest.mark.asyncio
async def test_explanation_endpoint_returns_grounded_response(client: AsyncClient) -> None:
    standard_id, _ = await seed_structural_steel(client)
    response = await client.post(
        "/api/v1/recommendations/explanation",
        json={"text": "hot rolled medium and high tensile structural steel", "standard_id": standard_id},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["explanation"]
    assert body["status"] in {"success", "unavailable", "backend_error"}


@pytest.mark.asyncio
async def test_detail_endpoints_return_real_data(client: AsyncClient) -> None:
    standard_id, _ = await seed_structural_steel(client)
    related = await client.get(f"/api/v1/recommendations/standards/{standard_id}/related")
    versions = await client.get(f"/api/v1/recommendations/standards/{standard_id}/version-history")
    compliance = await client.get(f"/api/v1/recommendations/standards/{standard_id}/compliance")
    sources = await client.get(f"/api/v1/recommendations/standards/{standard_id}/sources")
    mapping = await client.post(
        f"/api/v1/recommendations/standards/{standard_id}/mapping",
        json={"text": "hot rolled medium and high tensile structural steel"},
    )
    evidence = await client.post(
        f"/api/v1/recommendations/standards/{standard_id}/evidence",
        json={"text": "hot rolled medium and high tensile structural steel"},
    )
    assert related.status_code == versions.status_code == compliance.status_code == sources.status_code == 200
    assert mapping.status_code == evidence.status_code == 200
    assert related.json()["items"]
    assert versions.json()["items"]
    assert compliance.json()["items"]["qco"]
    assert sources.json()["items"]
    assert mapping.json()["items"]
    assert evidence.json()["items"]


@pytest.mark.asyncio
async def test_refine_and_tender_endpoints(client: AsyncClient) -> None:
    await seed_structural_steel(client)
    refine = await client.post(
        "/api/v1/recommendations/refine",
        json={
            "original_text": "structural steel",
            "refinement": "hot rolled medium and high tensile grades for building construction",
        },
    )
    tender = await client.post(
        "/api/v1/recommendations/tender",
        json={"text": "hot rolled medium and high tensile structural steel"},
    )
    assert refine.status_code == 200
    assert tender.status_code == 200
    assert refine.json()["requirement"]["original_text"] == "structural steel"
    assert "Additional requirement details" in refine.json()["requirement"]["combined_text"]
    assert "TENDER SPECIFICATION DRAFT" in tender.json()["specification"]
    assert tender.json()["disclaimer"]
