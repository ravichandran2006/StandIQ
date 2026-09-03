from dataclasses import dataclass, field
from typing import Any, Protocol

from app.application.documents import DocumentInput
from app.application.multilingual import LanguageMetadata


@dataclass(frozen=True)
class BoundingBox:
    left: float
    top: float
    right: float
    bottom: float

    def __post_init__(self) -> None:
        if self.left < 0 or self.top < 0 or self.right < self.left or self.bottom < self.top:
            raise ValueError("invalid bounding box coordinates")


@dataclass(frozen=True)
class OCRTextBlock:
    text: str
    confidence: float | None = None
    bounds: BoundingBox | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("OCR text block cannot be empty")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("OCR confidence must be between 0 and 1")


@dataclass(frozen=True)
class OCRPageResult:
    page_number: int
    extracted_text: str
    blocks: tuple[OCRTextBlock, ...] = ()
    language: LanguageMetadata | None = None
    confidence: float | None = None
    errors: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.page_number < 1:
            raise ValueError("OCR page number must be positive")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("OCR confidence must be between 0 and 1")
        if not self.extracted_text.strip() and not self.errors:
            raise ValueError("OCR page must contain text or an extraction error")


@dataclass(frozen=True)
class OCRDocumentResult:
    document_id: str
    pages: tuple[OCRPageResult, ...]
    errors: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.document_id.strip():
            raise ValueError("OCR document id is required")
        page_numbers = [page.page_number for page in self.pages]
        if len(page_numbers) != len(set(page_numbers)):
            raise ValueError("OCR page numbers must be unique")


class OCRProcessor(Protocol):
    async def process(self, document: DocumentInput) -> OCRDocumentResult:
        """Extract page-level text and evidence metadata from a document."""
