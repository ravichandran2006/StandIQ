Database connection or schema failures return 503 with `database_unavailable`; the API never exposes raw SQL errors.
# StandIQ Phase 3 API

Phase 3 exposes the first service-backed standards API on top of the Phase 2 SQLAlchemy model. No BIS ingestion, recommendation, OCR, RAG, or compliance decision logic is included.

## Request Flow

```text
HTTP request
  -> FastAPI router and Pydantic schema
  -> StandardService
  -> StandardRepository
  -> SQLAlchemy AsyncSession
  -> Neon PostgreSQL
```

The router owns HTTP concerns, the service owns transactions and business-level errors, and the repository owns database queries. SQLAlchemy models are not used as request contracts.

## Endpoints

| Method | Endpoint | Success | Purpose |
|---|---|---:|---|
| POST | `/api/v1/standards` | 201 | Create a standards metadata record |
| GET | `/api/v1/standards` | 200 | List standards with `offset`, `limit`, `status`, and title `search` |
| GET | `/api/v1/standards/{standard_id}` | 200 | Retrieve one standard |
| PATCH | `/api/v1/standards/{standard_id}` | 200 | Update editable metadata |
| DELETE | `/api/v1/standards/{standard_id}` | 204 | Delete a standard and dependent records according to FK policy |
| GET | `/api/v1/standards/{standard_id}/versions` | 200 | List recorded versions |
| GET | `/api/v1/standards/{standard_id}/relationships` | 200 | List explicit sourced relationships |
| GET | `/api/v1/health` | 200 | Report application and dependency state |

## Validation and Errors

Create requires a non-empty `is_number` and `title`; lengths are bounded by the domain columns. Update forbids unknown fields. Pagination accepts offsets from zero and limits from 1 through 100.

Errors use this shape:

```json
{
  "error": {
    "code": "not_found",
    "message": "Standard not found"
  }
}
```

Validation failures return 422 with `validation_error` and field details. Missing resources return 404. Unique-constraint conflicts return 409. Unexpected production errors return a generic 500 response without stack traces or database details.

## Important Rules

- A standard is identified by its unique IS number.
- The service commits create/update/delete transactions; read operations remain read-only.
- Duplicate standards are reported as conflicts rather than raw database errors.
- Version status is stored data. The API does not infer which version is latest.
- Relationships are returned with their explicit type and evidence note. Similarity is never promoted to `NORMATIVE` by this API.
- All production records are expected to carry source provenance in the Phase 2 model. Tests use synthetic `test-only` records.

## Local Commands

From `backend/`:

```powershell
.venv\Scripts\Activate.ps1
python -m pytest tests -q
alembic check
```

Set `DATABASE_URL` in the untracked root `.env` before running against Neon. The health endpoint performs a read-only connectivity check. Do not put credentials in `.env.example` or source control.

Before using standards endpoints against a fresh Neon database, apply the existing Phase 2 migration from `backend/` with `alembic upgrade head`. This changes schema state and is intentionally not run automatically by Phase 3.
