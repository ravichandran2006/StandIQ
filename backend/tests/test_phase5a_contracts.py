import pytest

from app.application.documents import DocumentInput, DocumentMetadata, DocumentProcessingError, DocumentType
from app.application.input import (
    InputProcessingPipeline,
    PlainTextOCRProcessor,
    UnicodeLanguageDetector,
)
from app.application.multilingual import LanguageMetadata, MultilingualInput, NormalizedText, RequirementTextExtraction
from app.application.ocr import BoundingBox, OCRDocumentResult, OCRPageResult, OCRTextBlock


def test_multilingual_input_preserves_original_and_metadata() -> None:
    original = "വ്യാവസായിക വയറിങ്ങിനായി കേബിൾ ട്രേ ആവശ്യമാണ്"
    language = LanguageMetadata(code="ml", name="Malayalam", confidence=0.98, script="Malayalam", detector="synthetic-test")
    normalized = NormalizedText(original_text=original, normalized_text=original.strip(), language=language, normalization_notes=("trimmed",))
    extraction = RequirementTextExtraction(original_text=original, normalized_text=normalized.normalized_text, language=language, extracted_text=normalized.normalized_text, confidence=0.91)

    assert normalized.original_text == original
    assert extraction.language.code == "ml"
    assert extraction.confidence == 0.91


@pytest.mark.parametrize("language_code", ["en", "ta", "hi", "ml", "kn", "bn"])
def test_language_metadata_supports_required_and_future_languages(language_code: str) -> None:
    metadata = LanguageMetadata(code=language_code, confidence=0.75)
    assert metadata.code == language_code


def test_invalid_multilingual_values_are_rejected() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        MultilingualInput(original_text="   ")
    with pytest.raises(ValueError, match="between 0 and 1"):
        LanguageMetadata(code="en", confidence=1.1)
    with pytest.raises(ValueError, match="normalized text cannot be empty"):
        NormalizedText(original_text="source", normalized_text="")


def test_document_metadata_and_content_are_traceable() -> None:
    content = b"synthetic tender text"
    metadata = DocumentMetadata(document_id="doc-test-1", filename="tender.txt", media_type="text/plain", document_type=DocumentType.TEXT, size_bytes=len(content), checksum="synthetic-checksum")
    document = DocumentInput(metadata=metadata, content=content)

    assert document.metadata.document_id == "doc-test-1"
    assert document.metadata.checksum == "synthetic-checksum"
    assert document.metadata.size_bytes == len(document.content)


def test_document_invalid_content_and_metadata_are_rejected() -> None:
    with pytest.raises(ValueError, match="document content cannot be empty"):
        DocumentInput(DocumentMetadata("doc", "empty.txt", "text/plain", DocumentType.TEXT, 0), b"")
    with pytest.raises(ValueError, match="does not match"):
        DocumentInput(DocumentMetadata("doc", "bad.txt", "text/plain", DocumentType.TEXT, 3), b"x")
    with pytest.raises(ValueError, match="filename is required"):
        DocumentMetadata("doc", "", "text/plain", DocumentType.TEXT, 0)


def test_ocr_page_preserves_page_language_confidence_and_position() -> None:
    language = LanguageMetadata(code="ta", name="Tamil", confidence=0.97, script="Tamil")
    box = BoundingBox(left=10, top=20, right=120, bottom=55)
    block = OCRTextBlock(text="செயற்கை விவரக்குறிப்பு", confidence=0.88, bounds=box)
    page = OCRPageResult(page_number=2, extracted_text=block.text, blocks=(block,), language=language, confidence=0.88)
    document = OCRDocumentResult(document_id="doc-test-2", pages=(page,))

    assert document.pages[0].page_number == 2
    assert document.pages[0].language.code == "ta"
    assert document.pages[0].blocks[0].bounds.right == 120


def test_ocr_errors_are_structured_and_page_traceable() -> None:
    page = OCRPageResult(page_number=3, extracted_text="", errors=("synthetic OCR timeout",))
    document = OCRDocumentResult(document_id="doc-test-3", pages=(page,), errors=("one page failed",))
    assert document.pages[0].errors == ("synthetic OCR timeout",)
    assert document.errors == ("one page failed",)

    with pytest.raises(ValueError, match="page numbers must be unique"):
        OCRDocumentResult(document_id="doc-test-4", pages=(page, page))


def test_ocr_invalid_geometry_confidence_and_missing_output_are_rejected() -> None:
    with pytest.raises(ValueError, match="invalid bounding box"):
        BoundingBox(left=10, top=10, right=5, bottom=20)
    with pytest.raises(ValueError, match="between 0 and 1"):
        OCRTextBlock(text="text", confidence=-0.1)
    with pytest.raises(ValueError, match="text or an extraction error"):
        OCRPageResult(page_number=1, extracted_text="")


def test_document_processing_error_carries_trace_context() -> None:
    error = DocumentProcessingError("synthetic parser failure", document_id="doc-test-5", page_number=4)
    assert str(error) == "synthetic parser failure"
    assert error.document_id == "doc-test-5"
    assert error.page_number == 4


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("text", "language_code"),
    [("cable tray specification", "en"), ("கேபிள் தட்டு", "ta"), ("केबल ट्रे", "hi"), ("കേബിൾ ട്രേ", "ml")],
)
async def test_unicode_language_detector_supports_required_scripts(text: str, language_code: str) -> None:
    result = await UnicodeLanguageDetector().detect(text)
    assert result.code == language_code
    assert result.detector == "unicode-script"


@pytest.mark.asyncio
async def test_input_pipeline_preserves_source_and_normalizes_text() -> None:
    original = "  കേബിൾ\n ട്രേ  ആവശ്യമാണ്  "
    result = await InputProcessingPipeline().process(MultilingualInput(original_text=original, source="tender"))

    assert result.original_text == original
    assert result.normalized_text == "കേബിൾ ട്രേ ആവശ്യമാണ്"
    assert result.extracted_text == result.normalized_text
    assert result.language.code == "ml"
    assert result.metadata["extractor"] == "plain-text"


@pytest.mark.asyncio
async def test_plain_text_ocr_returns_page_provenance() -> None:
    content = "தமிழ் தொழில்நுட்ப விவரக்குறிப்பு".encode("utf-8")
    document = DocumentInput(
        DocumentMetadata("doc-ocr", "tender.txt", "text/plain", DocumentType.TEXT, len(content)),
        content,
    )

    result = await PlainTextOCRProcessor().process(document)

    assert result.document_id == "doc-ocr"
    assert result.pages[0].extracted_text == content.decode("utf-8")
    assert result.pages[0].language.code == "ta"
    assert result.pages[0].metadata["processor"] == "plain-text"


@pytest.mark.asyncio
async def test_plain_text_ocr_rejects_unsupported_binary_format() -> None:
    content = b"%PDF-1.7"
    document = DocumentInput(
        DocumentMetadata("doc-pdf", "tender.pdf", "application/pdf", DocumentType.PDF, len(content)),
        content,
    )

    with pytest.raises(DocumentProcessingError, match="does not support"):
        await PlainTextOCRProcessor().process(document)
