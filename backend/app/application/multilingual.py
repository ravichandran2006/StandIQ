from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class LanguageMetadata:
    code: str
    name: str | None = None
    confidence: float | None = None
    script: str | None = None
    detector: str | None = None
    alternatives: tuple[tuple[str, float], ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("language code is required")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("language confidence must be between 0 and 1")


@dataclass(frozen=True)
class MultilingualInput:
    original_text: str
    source: str = "text"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.original_text.strip():
            raise ValueError("original text cannot be empty")


@dataclass(frozen=True)
class NormalizedText:
    original_text: str
    normalized_text: str
    language: LanguageMetadata | None = None
    normalization_notes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.original_text.strip():
            raise ValueError("original text cannot be empty")
        if not self.normalized_text.strip():
            raise ValueError("normalized text cannot be empty")


@dataclass(frozen=True)
class RequirementTextExtraction:
    original_text: str
    normalized_text: str
    language: LanguageMetadata
    extracted_text: str
    confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.original_text.strip() or not self.normalized_text.strip() or not self.extracted_text.strip():
            raise ValueError("requirement extraction text fields cannot be empty")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("extraction confidence must be between 0 and 1")


class LanguageDetector(Protocol):
    async def detect(self, text: str) -> LanguageMetadata:
        """Detect language without translating or changing the original text."""


class MultilingualTextNormalizer(Protocol):
    async def normalize(self, text: MultilingualInput) -> NormalizedText:
        """Normalize text while preserving the exact original input."""


class RequirementTextExtractor(Protocol):
    async def extract(self, text: NormalizedText) -> RequirementTextExtraction:
        """Extract requirement text; structured requirement understanding is later work."""
