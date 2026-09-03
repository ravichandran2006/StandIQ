# StandIQ Ingestion Framework (Phase 4B)

Status: Framework only. **REAL BIS DATA: NOT COLLECTED.** No undocumented BIS endpoint is used, no full BIS document is downloaded, and no production record is seeded.

## Phase 4A Findings

The current BIS portal exposes public metadata pages, but no documented public API was confirmed. Its browser application calls internal cross-origin services that are not approved for automated ingestion. Full standards documents are controlled/distributed content and are not stored by this framework. A future source adapter must be connected only after BIS or an authorized provider approves the access method and fields.

## Architecture

```text
Approved source adapter
  -> RawSourceRecord
  -> parser
  -> normalizer
  -> validator
  -> deduplicator/upsert repository
  -> Neon PostgreSQL
```

The framework is source-independent. It does not know a BIS URL, endpoint, credential, or document location. An adapter can later represent an approved API, JSON/JSONL export, CSV parser, or other authorized file source.

## Adapter Contract

`SourceAdapter.records(incremental: bool)` is an async iterator yielding:

- `source_type`
- `source_url`
- `external_identifier`
- raw object `payload`
- `retrieved_at`

`JsonFileSourceAdapter` currently accepts an approved JSON array/object or JSONL/NDJSON file. It is a local adapter for testing and future authorized exports only. It does not perform network access and does not make a file authoritative.

A future approved BIS adapter should:

1. identify the authorization/export agreement in configuration;
2. preserve the exact source URL or file identifier;
3. return the provider's stable external ID;
4. preserve raw payloads outside the normalized database if retention is permitted;
5. pass `incremental=True` through to an approved change/update mechanism;
6. fail loudly on unavailable or malformed source responses.

## Expected Metadata Format

The normalized standard bundle accepts these fields when supplied by the approved source:

```json
{
  "external_identifier": "provider-id",
  "is_number": "IS 123 : 2024",
  "title": "Standard title",
  "standard_type": "product",
  "publication_info": "provider supplied metadata",
  "review_info": null,
  "technical_committee": "provider supplied committee",
  "status": "active",
  "versions": [
    {
      "edition_label": "2024 edition",
      "edition_year": 2024,
      "publication_date": "2024-02-03",
      "is_current": true,
      "status": "active"
    }
  ],
  "amendments": [
    {
      "edition_label": "2024 edition",
      "amendment_label": "Amd 1",
      "title": "provider supplied title",
      "publication_date": "2024-03-04",
      "details": "provider supplied details"
    }
  ],
  "classifications": [{"scheme": "scheme", "code": "code", "title": "classification"}],
  "relationships": [{"target_is_number": "IS 456", "relationship_type": "REFERRED", "evidence_note": "explicit source statement"}],
  "certifications": [{"scheme_name": "scheme", "external_identifier": "id", "title": "record title"}],
  "qco_records": [{"identifier": "notification-id", "title": "record title"}],
  "crs_records": [{"identifier": "registration-id", "title": "record title"}],
  "hallmarking_rules": [{"identifier": "rule-id", "title": "record title"}]
}
```

Missing provider fields remain `NULL` or absent. The framework never invents values. Relationship types are accepted only from the explicit vocabulary (`REFERRED`, `NORMATIVE`, `TEST_METHOD`, `TERMINOLOGY`, `SAFETY`, `INSTALLATION`, `ALLIED`, `SUPERSEDES`, `SUPERSEDED_BY`, `RELATED`). Semantic similarity is never converted into a normative relationship.

## Normalization and Validation

- Collapse repeated whitespace and trim text.
- Normalize IS numbers to uppercase and consistent spacing around colons.
- Accept ISO and Indian day-first slash date formats and store Python dates.
- Normalize supported status aliases to lowercase values.
- Require source type, source URL, external identifier, IS number, and title.
- Reject unsupported statuses, relationship types, empty classifications, and self-references.
- Preserve source URLs and retrieval timestamps.

## Deduplication and Incremental Updates

- Source records deduplicate on `(source_type, external_identifier)`.
- Standards deduplicate on `is_number`.
- Versions deduplicate on `(standard_id, edition_year)` when a year exists, otherwise edition label.
- Amendments deduplicate on `(standard_version_id, amendment_label)`.
- Classifications deduplicate on `(scheme, code)`.
- Relationships deduplicate on `(source, target, relationship_type)`.
- Certification, QCO, CRS, and Hallmarking records use their Phase 2 stable identifiers.

A second ingestion updates changed authoritative fields and does not create duplicate rows. The incremental flag is passed to the adapter; the adapter must use only an approved provider change mechanism. The framework does not infer latest versions from local timestamps.

## Run Tracking and Failures

Every non-dry-run creates an `ingestion_runs` record. It records discovered, inserted, updated, skipped, failed counts, status, completion time, and an error summary. Each record is processed in a savepoint so one invalid record does not silently discard valid records. Adapter-level failures mark the run failed.

Dry-run parses and validates records and reports planned valid inserts without opening a database transaction or writing an ingestion run. It is safe for inspecting an approved export before persistence.

## Commands

From `backend/`:

```powershell
.venv\Scripts\Activate.ps1
python -m app.ingestion --file path\to\approved-export.json --dry-run
python -m app.ingestion --file path\to\approved-export.json --mode incremental
```

The CLI requires configured `DATABASE_URL` for non-dry-run operation. It does not create schemas; apply existing Alembic migrations separately with `alembic upgrade head`.

## Connecting an Approved BIS Source

After written permission and a stable approved interface are available, implement a new adapter under `app/ingestion/` that maps the provider response into `RawSourceRecord`. Do not modify the normalizer or repository to embed provider-specific URL logic. Add sanitized fixtures, source permission notes, parser tests, and a small controlled run. Only then configure the adapter in a command entry point.

## Access and Copyright Boundary

This framework intentionally does not use the undocumented BIS browser service calls discovered in Phase 4A. It does not bypass CAPTCHA, authentication, rate limits, robots restrictions, or distribution controls. It does not download or re-host full BIS standards. Metadata retention, derived-content retention, commercial/demo use, and automated access all require confirmation from BIS or the authorized provider for the selected source.
