# StandIQ

**Right Standards. Right Tenders.**

StandIQ is an AI-powered Indian standards intelligence system for procurement. The repository includes the React/FastAPI foundation, domain persistence, ingestion framework, multilingual text processing, and a deterministic evidence-aware text recommendation workflow. Recommendations use stored standards metadata and explicitly mark unsupported provenance as requiring verification.

## Stack

- React with Vite
- Python 3.13+ with FastAPI and Uvicorn
- Neon PostgreSQL through SQLAlchemy and `asyncpg`
- Pinecone, provider-neutral LLM, and configurable multilingual embeddings as optional later-phase adapters
- PaddleOCR as the production OCR adapter in a later phase

The backend is the only component that will access PostgreSQL. Docker and local PostgreSQL are not required.

## Setup

### Backend

```powershell
cd backend
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m scripts.check_config
```

Copy the root `.env.example` to `.env` and fill only the services you have configured. Never commit `.env`.

Start the API from the repository root:

```powershell
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

Health endpoint: `http://localhost:8000/api/v1/health`.
Recommendation endpoint: `POST http://localhost:8000/api/v1/recommendations` with `{ "text": "...", "language": "en" }`.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend calls `VITE_API_URL` or defaults to `http://localhost:8000`. Build it with:

```powershell
npm run build
```

## Environment variables

- `DATABASE_URL`: Neon PostgreSQL connection string.
- `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`: Pinecone configuration; connectivity and indexing remain unverified until credentials and an approved corpus are available.
- `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`: provider-neutral LLM configuration.
- `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`: multilingual embedding configuration.
- `APP_SECRET_KEY`: server-side application secret for later authenticated workflows.
- `LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.
- `CORS_ORIGINS`: comma-separated allowed browser origins.
- `APP_ENV`: environment name, such as `development` or `production`.

Missing external credentials produce `not_configured` component states; the application health endpoint remains available. No credential values are printed.

No authorized BIS dataset is bundled. Records used in tests are synthetic fixtures and must not be presented as BIS data. The recommendation endpoint abstains when no stored standard matches; compliance mappings remain `verification_required` and are not legal determinations.

## Tests

```powershell
backend\.venv\Scripts\python.exe -m pytest backend\tests -q

Push-Location backend
.venv\Scripts\python.exe -m scripts.check_config
Pop-Location
```

Frontend build:

```powershell
cd frontend
npm run build
npm test
```

## Architecture

See [docs/architecture.md](docs/architecture.md), [docs/gap-analysis.md](docs/gap-analysis.md), [docs/implementation-plan.md](docs/implementation-plan.md), and [backend/docs/MODEL_SELECTION.md](backend/docs/MODEL_SELECTION.md).
