# StandIQ Phase 5: Multilingual Input and OCR

Status: Provider-independent contracts plus a deterministic Unicode/text baseline. PaddleOCR runtime, translation, embeddings, Pinecone, RAG, BIS ingestion, ranking, and compliance decisions remain outside this phase.

## Boundaries

The foundation preserves the user/document source exactly and keeps provider interpretation separate:

```text
User text/document
  -> input contract
  -> language detector contract
  -> text normalizer contract
  -> requirement extraction contract
  -> future requirement pipeline

Document
  -> OCR processor contract
  -> page results and evidence positions
  -> future text normalization/extraction
```

No contract changes the original source. A later service may produce normalized text and extracted requirement text, but must retain the original text and language metadata.

## Multilingual Contracts

`LanguageMetadata` stores:

- BCP-47-style language code such as `en`, `ta`, `hi`, or `ml`;
- optional display name and script;
- confidence in the inclusive range 0 to 1;
- detector/provider name;
- alternative language candidates and scores;
- provider metadata.

`MultilingualInput` stores original user text, source, and metadata. Empty text is rejected.

`NormalizedText` stores both `original_text` and `normalized_text`, optional language metadata, normalization notes, and metadata.

`RequirementTextExtraction` stores original text, normalized text, extracted text, detected language, confidence, and metadata. It is deliberately text-level; structured technical requirement extraction belongs to a later phase.

The `LanguageDetector`, `MultilingualTextNormalizer`, and `RequirementTextExtractor` protocols are provider-independent async interfaces. They support English, Tamil, Hindi, Malayalam, and future Indian languages without hard-coded translation output.

## Document Contracts

`DocumentMetadata` preserves document ID, filename, media type, document type, byte size, optional page count, checksum, source, and metadata. Supported document types include PDF, Word, text, image, scanned tender, and technical specification.

`DocumentInput` combines metadata and bytes and rejects empty content or mismatched byte sizes. It is a processing input contract; storage/retention policy remains a later decision.

`DocumentProcessingError` carries document and optional page context without exposing document content.

## OCR Contracts

`OCRProcessor.process(DocumentInput)` is the PaddleOCR integration point. It returns an `OCRDocumentResult` containing:

- document ID;
- unique page-level results;
- document-level errors and metadata.

Each `OCRPageResult` contains page number, extracted text, blocks, detected language, aggregate confidence, page errors, and provider metadata. A page may contain either extracted text or a structured extraction error.

Each `OCRTextBlock` contains text, confidence, optional `BoundingBox`, and provider metadata. Coordinates are validated so negative or inverted geometry cannot enter downstream evidence mapping.

Page numbers and document IDs provide traceability from extracted text back to the uploaded document. Bounding boxes preserve positional evidence when the OCR provider supplies it.

## Supported Language Strategy

The baseline `UnicodeLanguageDetector` identifies the dominant Latin, Tamil, Hindi, or Malayalam script without changing source text. `BasicTextNormalizer` applies Unicode NFC and whitespace normalization, while `PlainTextRequirementExtractor` returns normalized text as a text-level extraction result with full source and language metadata. These adapters are deterministic fallbacks, not a benchmark result or a translation service.

Production rollout should benchmark candidate language detection and document-text handling on English, Tamil, Hindi, and Malayalam procurement examples, including short text, mixed scripts, and noisy OCR output.

Translation is not required as an initial dependency. Cross-language retrieval will be addressed only after the language/OCR evaluation and embedding-selection phase.

## PaddleOCR Integration Point

A future PaddleOCR adapter should implement `OCRProcessor` under infrastructure, convert PaddleOCR output into `OCRPageResult` and `OCRTextBlock`, preserve confidence/coordinates, and map failures to `DocumentProcessingError` or page-level errors. The current `PlainTextOCRProcessor` handles UTF-8 `text/plain` documents as one page and explicitly rejects unsupported PDF, Word, and image formats until that adapter is selected and installed.

The adapter must enforce input type/size limits, avoid logging document contents, and report unsupported formats and OCR failures explicitly. It must not silently turn low-confidence or empty output into valid requirements.

## Future Embedding Integration Point

After multilingual normalization and requirement extraction are evaluated, an application service can pass selected text to a future embedding provider. This phase creates no embedding interface implementation and no Pinecone dependency. Original text, normalized text, detected language, and OCR page provenance must remain available to that later boundary.

## Testing

Tests use synthetic strings, bytes, language metadata, page numbers, and coordinates only. They cover required languages and future language codes, original-text preservation, confidence bounds, document size validation, OCR geometry, page traceability, duplicate page rejection, structured extraction errors, and processing-error context.
