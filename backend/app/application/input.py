import re
import unicodedata

from app.application.documents import DocumentInput, DocumentProcessingError, DocumentType
from app.application.multilingual import (
    LanguageDetector,
    LanguageMetadata,
    MultilingualInput,
    MultilingualTextNormalizer,
    NormalizedText,
    RequirementTextExtraction,
    RequirementTextExtractor,
)
from app.application.ocr import OCRDocumentResult, OCRPageResult, OCRProcessor


_LANGUAGE_RANGES: tuple[tuple[str, str, str], ...] = (
    ("ml", "Malayalam", "Malayalam"),
    ("ta", "Tamil", "Tamil"),
    ("hi", "Hindi", "Devanagari"),
)


class InputProcessingError(Exception):
    """Raised when an input cannot be processed by the selected adapter."""


class UnicodeLanguageDetector(LanguageDetector):
    """Detect the dominant supported script without altering the input."""

    async def detect(self, text: str) -> LanguageMetadata:
        if not text.strip():
            raise InputProcessingError("Cannot detect language from empty text")

        counts = {code: 0 for code, _, _ in _LANGUAGE_RANGES}
        latin_count = 0
        for character in text:
            codepoint = ord(character)
            if "A" <= character <= "Z" or "a" <= character <= "z":
                latin_count += 1
            for code, _, script in _LANGUAGE_RANGES:
                if _in_script(codepoint, script):
                    counts[code] += 1

        code, count = max(counts.items(), key=lambda item: item[1])
        total = sum(counts.values()) + latin_count
        if latin_count > count and latin_count > 0:
            return LanguageMetadata(code="en", name="English", confidence=latin_count / total, script="Latin", detector="unicode-script")
        if count == 0 or total == 0:
            return LanguageMetadata(code="und", name="Undetermined", confidence=0.0, detector="unicode-script")
        name, script = next((name, script) for candidate, name, script in _LANGUAGE_RANGES if candidate == code)
        return LanguageMetadata(code=code, name=name, confidence=count / total, script=script, detector="unicode-script")


class BasicTextNormalizer(MultilingualTextNormalizer):
    """Apply Unicode NFC and whitespace normalization while retaining the source."""

    async def normalize(self, text: MultilingualInput) -> NormalizedText:
        original = text.original_text
        normalized = unicodedata.normalize("NFC", original)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        notes: list[str] = []
        if normalized != original:
            notes.append("unicode-and-whitespace-normalized")
        return NormalizedText(
            original_text=original,
            normalized_text=normalized,
            normalization_notes=tuple(notes),
            metadata={"source": text.source, **text.metadata},
        )


class PlainTextRequirementExtractor(RequirementTextExtractor):
    """Return normalized text as the Phase 5 text-level extraction result."""

    def __init__(self, language_detector: LanguageDetector | None = None) -> None:
        self.language_detector = language_detector or UnicodeLanguageDetector()

    async def extract(self, text: NormalizedText) -> RequirementTextExtraction:
        language = text.language or await self.language_detector.detect(text.normalized_text)
        return RequirementTextExtraction(
            original_text=text.original_text,
            normalized_text=text.normalized_text,
            language=language,
            extracted_text=text.normalized_text,
            confidence=1.0,
            metadata={"extractor": "plain-text"},
        )


class PlainTextOCRProcessor(OCRProcessor):
    """Process UTF-8 text documents; binary OCR is intentionally explicit."""

    supported_types = frozenset({DocumentType.TEXT, DocumentType.TECHNICAL_SPECIFICATION})

    def __init__(self, language_detector: LanguageDetector | None = None) -> None:
        self.language_detector = language_detector or UnicodeLanguageDetector()

    async def process(self, document: DocumentInput) -> OCRDocumentResult:
        if document.metadata.document_type not in self.supported_types or document.metadata.media_type != "text/plain":
            raise DocumentProcessingError(
                "plain-text OCR adapter does not support this document format",
                document_id=document.metadata.document_id,
            )
        try:
            text = document.content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DocumentProcessingError(
                "document is not valid UTF-8 text",
                document_id=document.metadata.document_id,
            ) from exc
        if not text.strip():
            raise DocumentProcessingError("document contains no text", document_id=document.metadata.document_id)
        language = await self.language_detector.detect(text)
        page = OCRPageResult(
            page_number=1,
            extracted_text=text,
            language=language,
            confidence=1.0,
            metadata={"processor": "plain-text"},
        )
        return OCRDocumentResult(document_id=document.metadata.document_id, pages=(page,), metadata={"processor": "plain-text"})


class InputProcessingPipeline:
    """Run language detection, normalization, and text-level extraction in order."""

    def __init__(
        self,
        language_detector: LanguageDetector | None = None,
        normalizer: MultilingualTextNormalizer | None = None,
        extractor: RequirementTextExtractor | None = None,
    ) -> None:
        detector = language_detector or UnicodeLanguageDetector()
        self.normalizer = normalizer or BasicTextNormalizer()
        self.extractor = extractor or PlainTextRequirementExtractor(detector)
        self.language_detector = detector

    async def process(self, text: MultilingualInput) -> RequirementTextExtraction:
        detected = await self.language_detector.detect(text.original_text)
        normalized = await self.normalizer.normalize(text)
        normalized = NormalizedText(
            original_text=normalized.original_text,
            normalized_text=normalized.normalized_text,
            language=detected,
            normalization_notes=normalized.normalization_notes,
            metadata=normalized.metadata,
        )
        return await self.extractor.extract(normalized)


def _in_script(codepoint: int, script: str) -> bool:
    if script == "Malayalam":
        return 0x0D00 <= codepoint <= 0x0D7F
    if script == "Tamil":
        return 0x0B80 <= codepoint <= 0x0BFF
    if script == "Devanagari":
        return 0x0900 <= codepoint <= 0x097F
    return False
