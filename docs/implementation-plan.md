# StandIQ Implementation Plan

This roadmap is intentionally ordered around authority, evidence, and independently testable stages. No phase after Phase 0 has been started.

## Phase Matrix

| Phase | Objective | Dependencies | Major files | APIs | Tests | Expected result | Risks |
|---|---|---|---|---|---|---|---|
| 0. Repository audit and architecture validation | Establish verified baseline and boundaries | Repository and toolchain access | `docs/gap-analysis.md`, `docs/architecture.md` | None | Audit checks | This audit and roadmap | Empty baseline; authority unknown |
| 1. Foundation and environment | Create React/FastAPI shells, settings, quality tooling | Python, Node/npm; choose TS/JS | `backend/app`, `frontend/src`, `.env.example`, lockfiles | Health/readiness | Smoke, lint, type, unit | Reproducible local foundation | Dependency/version drift |
| 2. PostgreSQL domain model | Define evidence-aware relational model and migrations | Neon `DATABASE_URL`; Phase 1 settings | `backend/app/domain`, `backend/app/infrastructure/db`, migrations | Analysis/result persistence | Model, migration, repository, DB integration | Queryable system of record | Schema churn, incomplete provenance |
| 3. Automated BIS ingestion | Ingest only permitted verified BIS metadata | Official-source investigation, schema | `infrastructure/sources/bis`, ingestion jobs | Ingestion status/admin boundary | Parser, fixture, idempotency, provenance | Reproducible source records | No API, access restrictions, licensing |
| 4. Amendments, versions and relationships | Model authoritative change and relation data | Phase 3 records and sources | `domain/standards`, migrations, source adapters | Standard detail/history | Version, amendment, relationship tests | Evidence-backed graph-like relations in SQL | Conflicting/incomplete source data |
| 5. Multilingual input and OCR | Process text and PDF/image inputs | PaddleOCR; language benchmark set | `application/input`, OCR/language adapters | Text/document analysis | English/Malayalam/Tamil/Hindi, OCR fixtures | Structured multilingual input | OCR quality, tables, unsupported scans |
| 6. Embeddings and Pinecone | Create versioned multilingual vector index | Embedding selection, Pinecone credentials | `infrastructure/embeddings`, `infrastructure/vector` | Index/reindex operations | Dimension, metadata, failure/retry | Rebuildable semantic index | Cost, vendor outage, model drift |
| 7. Hybrid retrieval | Combine metadata filters, lexical/semantic search | Phases 2, 4, 6 | `application/retrieval`, repositories | Candidate search | Labeled retrieval cases | Auditable candidate set | Sparse corpus and poor recall |
| 8. Applicability ranking | Score candidates from structured requirements and evidence | Retrieval and requirement schema | `application/ranking`, domain scoring | Ranked candidates | Ranking fixtures, abstention | Evidence-linked ranking | Bias, score misinterpretation |
| 9. Related/normative expansion | Expand verified relations and allied standards | Phase 4 and ranked candidates | `application/relationships` | Related standards | Relation traversal and cycle cases | Traceable related set | Relationship gaps or cycles |
| 10. Certification + CRS + QCO + Hallmarking | Add evidence-backed compliance checks | Official rule sources | `domain/compliance`, source adapters | Compliance evaluation | Positive, negative, unknown, stale evidence | Explicit applicability statuses | Regulatory changes; must abstain |
| 11. Latest version and amendment validation | Validate current status at analysis time | Version/amendment source data | `application/validation` | Freshness/validation | Stale/conflict/unavailable cases | Current-status evidence | Source lag and conflicting records |
| 12. Explainable recommendation engine | Combine pipeline output into explainable result | Phases 5-11 | `application/recommendations`, schemas | Analyze requirement/document | Contract and evidence tests | Recommendation with mappings and citations | Hallucinated explanations |
| 13. Tender-ready output | Produce structured guidance and downloadable report | Recommendation schema; wording review | `application/reports`, templates | Report generation/download | Snapshot, missing-info, export tests | Data-driven tender report | Overstating legal requirements |
| 14. Final React UI | Build responsive workflow and result views | Stable API contracts | `frontend/src/features`, pages, components | API client integration | Component, accessibility, browser tests | Usable desktop-first UI | UI drift and complex states |
| 15. End-to-end integration | Exercise text and upload workflows | Backend, frontend, managed services | `tests/e2e`, CI configuration | Full workflow | English/Malayalam/Tamil/Hindi E2E | Demonstrable complete flow | External-service flakiness |
| 16. Security and reliability | Harden multi-user operation | Integrated system | auth, limits, logging, dependency config | Auth/error/health behavior | Security, abuse, timeout, failure tests | Safe operational baseline | Secret leakage, DoS, PII |
| 17. Evaluation | Measure quality with labeled corpus | Evaluation dataset and rubric | `evaluation/`, report docs | Evaluation runner | Retrieval/ranking/OCR/multilingual metrics | Honest benchmark results | Dataset bias; no unsupported claims |
| 18. Deployment | Deploy frontend/backend and managed integrations | Hosting, secrets, monitoring decisions | deployment docs, CI/CD | Production health | Deployment smoke and rollback | Repeatable deployment | Cost, quotas, region limits |
| 19. Final audit and jury readiness | Verify requirements, demo path, evidence and risks | All prior phases | README, runbook, audit checklist | Demo/report workflow | Full regression and manual review | Reproducible jury demonstration | Last-minute source/model changes |

## Model Selection Gate

Before Phase 6 and Phase 8, benchmark candidate LLMs, multilingual embeddings, PaddleOCR language models, language detectors, and optional rerankers against the same held-out procurement set. Record accuracy, evidence adherence, multilingual behavior for English/Malayalam/Tamil/Hindi, technical-document handling, latency, cost, reliability, API/deployment availability, and licensing. Selection is a documented decision, not a popularity default.

## Phase 1 Exit Criteria

- React and FastAPI start locally with documented commands.
- Environment variables load from a safe example file; no real secrets are committed.
- Health and readiness endpoints are covered by tests.
- Linting, formatting, type checking where selected, and unit tests run in a clean environment.
- Database and external-service clients are interfaces or disabled adapters; no invented BIS integration is added.
- README documents setup and explicitly states that local PostgreSQL and Docker are not required.
