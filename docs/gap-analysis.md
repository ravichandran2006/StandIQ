# StandIQ Phase 0 Gap Analysis

Date: 2026-09-02
Status: Phase 0 audit

## Audit Basis

The repository root contains only two empty directories: `backend/` and `frontend/`. No files, package manifests, source code, tests, assets, Git metadata, environment files, or documentation were present. Findings marked UNKNOWN or REQUIRES VERIFICATION must not be treated as implemented capabilities.

## Category Assessment

| Category | Already implemented | Partially implemented | Missing | Incorrect / needs redesign | Dependencies / verification |
|---|---|---|---|---|---|
| A. Frontend | None | None | React app, routing, forms, upload UI, results UI, accessibility, responsive layout | No implementation to redesign | Node/npm available; choose TypeScript or JavaScript in Phase 1 |
| B. Backend | None | None | FastAPI app, layered modules, validation, error handling, health endpoints | No implementation to redesign | Python available; define API contract before coding |
| C. Database | None | None | Neon PostgreSQL schema, migrations, repositories, audit/provenance fields | Do not add local PostgreSQL | Neon project and `DATABASE_URL` required later; schema requires design |
| D. Vector Database | None | None | Pinecone index, namespaces, embedding metadata, sync/rebuild process | Do not use keyword-only retrieval | Pinecone account/API key and index design required; verify current SDK |
| E. LLM | None | None | Provider adapter, structured extraction, explanation prompts, retries and evidence constraints | LLM must not be compliance authority | Candidate comparison and provider availability require verification |
| F. Embeddings | None | None | Multilingual embedding pipeline and versioned vectors | English-only retrieval would be incorrect | Benchmark candidate models on Indian-language queries |
| G. OCR | None | None | PaddleOCR integration, PDF/image handling, confidence and failure states | No OCR exists | Verify supported languages, formats, and runtime requirements |
| H. Multilingual Processing | None | None | Language detection, Malayalam/Tamil/Hindi test fixtures, Unicode-safe processing | Translation API is not required initially | Verify model quality and script coverage |
| I. BIS Integration | None | None | Authorized-source adapter, provenance, retrieval timestamps, source URLs | Invented endpoints or blind crawling are prohibited | Official access methods, licensing, robots, and permitted datasets require verification |
| J. Amendments | None | None | Amendment/version entities and validation workflow | Never infer amendment status from LLM output | BIS source and change-history evidence require verification |
| K. Standards Relationships | None | None | Normative, test, terminology, safety, installation, allied, and superseding relationships | Relationships must be authoritative, not invented | Relationship source coverage and licensing require verification |
| L. Certification | None | None | Evidence-backed BIS Product Certification applicability | No certification claims may be generated without evidence | Scheme data and notification authority require verification |
| M. CRS | None | None | CRS applicability data and evidence model | No CRS mapping exists | Official/current CRS source requires verification |
| N. QCO | None | None | QCO applicability, notification/version/effective-date model | No QCO mapping exists | Government/BIS notification sources require verification |
| O. Hallmarking | None | None | Product/material/jurisdiction applicability checks | No Hallmarking rule exists | Current official rules require verification |
| P. Recommendation Engine | None | None | Requirement schema, hybrid retrieval, ranking, confidence and abstention | Hard-coded results would be incorrect | Requires validated standards corpus and evaluation set |
| Q. Explainability | None | None | Evidence snippets, score factors, requirement-to-standard mapping, provenance labels | AI interpretation must be separated from source fact | UX and citation behavior require testing |
| R. Tender Output | None | None | Structured tender guidance, ambiguity list, report export | No output may present unverified facts as requirements | Legal/procurement wording needs review |
| S. Security | None | None | Secret management, auth strategy, upload limits, PII policy, audit logs, dependency scanning | Never place secrets in frontend or source | Deployment provider and identity approach require decision |
| T. Testing | None | None | Unit, integration, API, database, ingestion, retrieval, ranking, multilingual, OCR, compliance, E2E, security tests | No passing test claim is possible | Need fixtures, test database strategy, and evaluation corpus |
| U. Deployment | None | None | Frontend/backend hosting, Neon/Pinecone configuration, observability, CI/CD | Docker/local PostgreSQL are not required by current brief | Hosting, domains, limits, and secrets manager require decision |
| V. Documentation | None | None | README, architecture, runbook, provenance policy, API docs, evaluation report | No documentation exists | Keep docs synchronized with implementation |

## Environment Audit

- Git: `2.54.0.windows.1` executable, but the workspace root is not a Git repository.
- Python: `3.13.14` available.
- Node.js: `v24.15.0` available.
- npm: `11.12.1` available.
- Docker: not installed/on PATH; this is consistent with the current requirement.
- `psql`: not installed/on PATH; local PostgreSQL is not required.
- Python virtual environment: not found.
- Node dependencies: no `node_modules` directory found.
- Frontend build: not run; no package manifest or source exists.
- Backend start: not run; no Python application or dependency file exists.
- Tests: not run; no test files or test configuration exists.
- Editor diagnostics: no errors found for the workspace.

## Required External Services Later

1. Neon PostgreSQL and a `DATABASE_URL`.
2. Pinecone and an index API key/environment.
3. One selected LLM provider and server-side API key.
4. A selected multilingual embedding runtime/provider and model artifact or API access.
5. BIS and other official/authorized data sources, subject to access and permitted-use verification.
6. PaddleOCR runtime; no separate OCR API key is expected.

Redis, Neo4j, a translation API, message queues, Docker PostgreSQL, and microservices are not justified at Phase 0.

## Credentials Needed Before Phase 1

Do not provide credentials in the repository. Phase 1 will need a development configuration strategy and placeholders for `DATABASE_URL`, `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`, `LLM_API_KEY`, and application secret material. Actual BIS access credentials, if any, are UNKNOWN and must be established only after official-source verification.

## Recommended Model Candidates

These are candidates, not selections. Benchmarking is required before commitment.

- LLM: OpenAI GPT-4.1/4.1-mini, Google Gemini 2.5 Flash/Pro, and a suitable Groq-hosted model such as Llama 4 where API availability and multilingual technical quality are verified. Compare extraction accuracy, evidence adherence, latency, rate limits, cost, and structured-output support.
- Embeddings: multilingual-e5-large, BGE-M3, and Cohere Embed Multilingual. Compare English, Malayalam, Tamil, and Hindi retrieval using a labeled standards-query set; verify licensing, dimensions, context limits, and Pinecone compatibility.
- OCR: PaddleOCR as required by the brief. Verify language models, scanned-PDF behavior, table handling, confidence output, and CPU deployment cost.
- Language detection: fastText lid.176, Lingua, and a model-based fallback. Compare short noisy procurement text across required languages; do not rely on a single detector for script ambiguity.
- Optional reranker: bge-reranker-v2-m3 or a hosted multilingual reranker. Add only if evaluation shows hybrid retrieval needs it; compare latency and license constraints.

No accuracy percentage is claimed because no evaluation has been run.

## Phase 1 Starting Point

Create the project foundations: choose frontend language, establish Python environment and dependency locking, create FastAPI and React health-check shells, add structured settings loaded from environment variables, configure lint/type/test tooling, and define the first domain/API contracts. Do not ingest or invent BIS data until the authority and access investigation is complete.
