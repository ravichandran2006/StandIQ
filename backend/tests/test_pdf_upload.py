import io
import pytest
from httpx import ASGITransport, AsyncClient
from fpdf import FPDF
from pypdf import PdfWriter

from app.main import create_app
from app.settings import Settings


def make_pdf_bytes(text: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 10, text)
    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


def make_blank_pdf_bytes() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from app.domain.models.base import Base


@pytest.fixture
async def client(tmp_path: Path):
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'pdf_test.db'}"
    settings = Settings(_env_file=None, app_env="test", database_url=database_url)
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    app = create_app(settings)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    await engine.dispose()


@pytest.mark.asyncio
async def test_pdf_upload_stainless_steel(client: AsyncClient):
    pdf_bytes = make_pdf_bytes("Stainless steel wire for reinforced concrete structures conforming to BIS standards")
    response = await client.post(
        "/api/v1/recommendations/upload",
        files={"file": ("stainless_steel_spec.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert "requirement" in body
    assert "standards" in body
    assert "summary" in body
    assert body["document"] is not None
    assert body["document"]["filename"] == "stainless_steel_spec.pdf"
    assert body["document"]["page_count"] >= 1
    assert body["document"]["extracted_text_length"] > 0
    assert "Stainless steel wire" in body["requirement"]["original_text"]


@pytest.mark.asyncio
async def test_pdf_upload_water_purifier(client: AsyncClient):
    pdf_bytes = make_pdf_bytes("Water purifier and drinking water supply systems for institutional use")
    response = await client.post(
        "/api/v1/recommendations/upload",
        files={"file": ("water_purifier_tender.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["document"]["filename"] == "water_purifier_tender.pdf"
    assert "Water purifier" in body["requirement"]["original_text"]


@pytest.mark.asyncio
async def test_pdf_upload_documents_alias_endpoint(client: AsyncClient):
    pdf_bytes = make_pdf_bytes("Stainless steel wire for construction")
    response = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("spec.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["document"]["filename"] == "spec.pdf"


@pytest.mark.asyncio
async def test_blank_pdf_returns_no_readable_text_error(client: AsyncClient):
    blank_pdf = make_blank_pdf_bytes()
    response = await client.post(
        "/api/v1/recommendations/upload",
        files={"file": ("blank.pdf", blank_pdf, "application/pdf")},
    )
    assert response.status_code == 400
    body = response.json()
    expected = "No readable text found in the uploaded document."
    assert body.get("detail") == expected or body.get("error", {}).get("message") == expected


@pytest.mark.asyncio
async def test_corrupt_pdf_returns_unable_to_extract_error(client: AsyncClient):
    corrupt_pdf = b"%PDF-1.4 corrupt junk content that cannot be parsed by pdf reader %%%"
    response = await client.post(
        "/api/v1/recommendations/upload",
        files={"file": ("corrupt.pdf", corrupt_pdf, "application/pdf")},
    )
    assert response.status_code == 400
    body = response.json()
    expected = "Unable to extract text from the uploaded PDF."
    assert body.get("detail") == expected or body.get("error", {}).get("message") == expected


@pytest.mark.asyncio
async def test_unsupported_file_format(client: AsyncClient):
    response = await client.post(
        "/api/v1/recommendations/upload",
        files={"file": ("notes.exe", b"MZbinaryexecutable", "application/x-msdownload")},
    )
    assert response.status_code == 400
    body = response.json()
    assert "Only PDF files are supported" in (body.get("detail") or body.get("error", {}).get("message", ""))


@pytest.mark.asyncio
async def test_empty_content_returns_error(client: AsyncClient):
    response = await client.post(
        "/api/v1/recommendations/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400
    body = response.json()
    expected = "No readable text found in the uploaded document."
    assert body.get("detail") == expected or body.get("error", {}).get("message") == expected
