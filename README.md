# StandIQ

**Right Standards. Right Tenders.**

StandIQ is an AI-powered Indian standards intelligence system for procurement. The repository currently includes the React/FastAPI foundation, domain persistence, ingestion framework, and a deterministic Phase 5 multilingual/text-input baseline. PaddleOCR runtime, embeddings, retrieval, ranking, compliance intelligence, and recommendation workflows remain deferred.

## Stack

- React with Vite
- Python 3.13+ with FastAPI and Uvicorn
- Neon PostgreSQL through SQLAlchemy and `asyncpg`
- Pinecone, provider-neutral LLM, and configurable multilingual embeddings in later phases
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
- `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`: Pinecone configuration; the index is not created or populated in Phase 1.
- `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`: provider-neutral LLM configuration.
- `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`: multilingual embedding configuration.
- `APP_SECRET_KEY`: server-side application secret for later authenticated workflows.
- `LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.
- `CORS_ORIGINS`: comma-separated allowed browser origins.
- `APP_ENV`: environment name, such as `development` or `production`.

Missing external credentials produce `not_configured` component states; the application health endpoint remains available. No credential values are printed.

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
