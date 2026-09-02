# StandIQ Database Foundation

Status: Phase 2 complete. The schema is structural only; no real BIS, certification, QCO, CRS, or Hallmarking records are inserted.

## Architecture

```text
FastAPI API
  -> application use case
  -> repository interface/implementation
  -> SQLAlchemy async session
  -> Neon PostgreSQL
```

API routes must not issue SQL directly. The database is the system of record for verified metadata, provenance, relationships, and future analysis history. Pinecone is deferred and will never be authoritative.

## Entity Relationships

- `standards` stores the stable IS-number identity, title, broad type, publication/review information, technical committee, status, optional superseding standard, and source record.
- `standard_versions` belongs to a standard and stores edition labels, optional year/date, current/status fields, and source evidence.
- `amendments` belongs to a standard version and stores an amendment label, details, date, and source evidence.
- `classifications` stores a classification scheme/code; `standard_classifications` is the normalized many-to-many link to standards.
- `standard_relationships` connects two different standards with an explicit relationship type and evidence source. Similarity is not automatically normative.
- `source_records` stores source URL/identifier, status, retrieval/check timestamps, content hash, and optional ingestion run.
- `ingestion_runs` records source processing lifecycle and discovered/inserted/updated/skipped/failed counts.
- `certifications` stores externally sourced certification scheme records without making applicability decisions.
- `qco_records` and `qco_mappings` store notification records and their explicit standard mappings.
- `crs_records` and `crs_mappings` store CRS records and their explicit standard mappings.
- `hallmarking_rules` stores externally sourced rules and material notes without evaluating a request.

The model intentionally does not include requirements, recommendations, embeddings, OCR results, or compliance decision outcomes yet. Those belong to later phases after their contracts and authority sources are defined.

## Integrity Rules

- Primary keys are generated UUID strings at the ORM boundary.
- IS numbers are unique in `standards`.
- A source type plus external identifier is unique in `source_records`.
- A standard has at most one version per recorded edition year when a year is supplied; the database does not infer which version is latest.
- Amendment labels are unique within a standard version.
- A relationship pair and relationship type are unique, and a standard cannot relate to itself.
- Classification scheme/code pairs, certification scheme/external IDs, QCO notification numbers, CRS registration numbers, and Hallmarking rule identifiers are unique.
- Foreign keys use cascade/delete-set-null behavior appropriate to dependent records and provenance retention.

## Important Indexes

- IS number uniqueness and title/status lookup on `standards`.
- Edition year and standard ID lookup on `standard_versions`.
- Standard version lookup on `amendments`.
- Source type/external identifier, ingestion run, and source identifiers on `source_records`.
- Source/target relationship lookups and target relationship type on `standard_relationships`.
- Classification, QCO, CRS, certification, and Hallmarking source/mapping foreign keys.

Indexes are limited to the fields used by identity, provenance, relationship, and future retrieval filters. Full-text and vector indexes are intentionally deferred.

## Migrations

Run from `backend/` with the virtual environment active:

```powershell
.venv\Scripts\Activate.ps1
alembic upgrade head
alembic current
alembic downgrade base
```

The initial revision is `f60a72e9a0ac_create_phase_2_domain_schema.py`. It is reproducible and imports the same SQLAlchemy metadata used by the application.

For Neon, set `DATABASE_URL` in a local untracked `.env` file. The Alembic environment reads it and uses the configured async driver. Do not manually change Neon tables outside migrations.

## Local Validation Strategy

No local PostgreSQL or Docker is used. When Neon is not configured, model/repository tests use an in-memory SQLite database through `aiosqlite`, with foreign-key enforcement enabled. SQLite validates ORM relationships and constraints; Neon-specific connectivity remains `NOT CONFIGURED` until a real `DATABASE_URL` is supplied.

## Repository Layout

```text
backend/
  alembic.ini
  alembic/env.py
  alembic/versions/
  app/domain/models/
  app/infrastructure/database.py
  app/infrastructure/repositories/standards.py
  tests/test_phase2_database.py
```
