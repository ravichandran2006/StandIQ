from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class DocumentType(StrEnum):
    PDF = "pdf"
    WORD = "word"
    TEXT = "text"
    IMAGE = "image"
    SCANNED_TENDER = "scanned_tender"
    TECHNICAL_SPECIFICATION = "technical_specification"


@dataclass(frozen=True)
class DocumentMetadata:
    document_id: str
    filename: str
    media_type: str
    document_type: DocumentType
    size_bytes: int
    page_count: int | None = None
    checksum: str | None = None
    source: str = "upload"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.document_id.strip():
            raise ValueError("document id is required")
        if not self.filename.strip():
            raise ValueError("filename is required")
        if self.size_bytes < 0:
            raise ValueError("document size cannot be negative")
        if self.page_count is not None and self.page_count < 1:
            raise ValueError("page count must be positive")


@dataclass(frozen=True)
class DocumentInput:
    metadata: DocumentMetadata
    content: bytes

    def __post_init__(self) -> None:
        if not self.content:
            raise ValueError("document content cannot be empty")
        if self.metadata.size_bytes != len(self.content):
            raise ValueError("document size does not match content length")


class DocumentProcessingError(Exception):
    def __init__(self, message: str, *, document_id: str | None = None, page_number: int | None = None) -> None:
        super().__init__(message)
        self.document_id = document_id
        self.page_number = page_number
