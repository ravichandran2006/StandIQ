# StandIQ Target Architecture

Status: Phase 0 design; implementation has not started.

## Principles

- BIS or another verified official/authorized source is authoritative for standards and compliance facts.
- LLM output is interpretation, extraction, ranking support, or explanation. It cannot create standards, relationships, versions, amendments, or compliance obligations.
- Every source fact stores source URL or identifier, retrieval timestamp, provenance type, and evidence status.
- Services fail safely. Unknown, unavailable, conflicting, or insufficient evidence results in an explicit verification state.
- The first deployment is a modular monolith with clean boundaries, not a collection of microservices.

## System Flow

```text
User
  -> React frontend
  -> FastAPI API
  -> Input processing
       - language detection
       - document validation and parsing
       - PaddleOCR for scanned PDFs/images
       - multilingual normalization
  -> Requirement understanding
       - schema validation
       - LLM/NLP extraction
       - ambiguity detection
  -> Hybrid retrieval
       - PostgreSQL metadata filters
       - multilingual embeddings
       - Pinecone semantic search
       - optional lexical search/reranking
  -> Candidate standards
  -> Evidence-backed applicability ranking
  -> Authoritative relationship expansion
       - normative/referred, test, terminology, safety, installation, allied, superseding
  -> Version and amendment validation
  -> Compliance intelligence
       - BIS Product Certification, QCO, CRS, Hallmarking
  -> Explainable recommendation
  -> Tender-ready output and report
```

## Logical Layers

- `presentation`: React views and FastAPI routers; no provider-specific business logic.
- `application`: use cases such as analyze requirement, analyze document, retrieve candidates, validate evidence, and generate report.
- `domain`: requirements, standards, evidence, relationships, versions, compliance determinations, recommendation scores, and explicit uncertainty states.
- `infrastructure`: PostgreSQL repositories, Pinecone adapter, model providers, PaddleOCR adapter, official-source connectors, storage, and observability.
- `tests`: unit tests for domain/application logic and contract/integration tests for adapters.

A likely future layout is:

```text
backend/app/{api,application,domain,infrastructure,settings}
backend/tests/{unit,integration,api,fixtures}
frontend/src/{components,features,pages,api,types}
docs/
```

Names remain subject to the Phase 1 foundation decision.

## Data Model Boundaries

Core entities should include `analysis_request`, `input_document`, `extracted_requirement`, `standard`, `standard_version`, `amendment`, `standard_relationship`, `compliance_rule`, `evidence_record`, `recommendation`, `requirement_mapping`, and `report`.

A compliance or relationship record must distinguish:

- authoritative source fact;
- AI interpretation or inferred match;
- confidence and evidence sufficiency;
- current verification state;
- source and retrieval timestamp.

PostgreSQL is the system of record for metadata, relationships, evidence, analysis results, and audit data. Pinecone stores versioned vectors with stable metadata IDs; it is not the authority and must be rebuildable.

## Request Flows

### Multilingual text

Malayalam, Tamil, Hindi, or English input -> language detection -> structured requirement extraction -> multilingual embedding -> Pinecone retrieval -> PostgreSQL metadata/evidence validation -> ranking -> relationship expansion -> version/amendment checks -> compliance checks -> explainable result.

### Uploaded document

PDF/image -> file/type/size validation -> text extraction or PaddleOCR -> language detection -> requirement extraction -> same pipeline. OCR failures, low confidence, unsupported files, and empty extraction must return actionable non-success states rather than fabricated results.

## API Responsibilities

Initial contracts should cover health/readiness, requirement analysis, document analysis, analysis status/result, and report download. Authentication, authorization, rate limits, upload limits, and request correlation IDs must be added before multi-user deployment.

Routers validate transport data and map errors. Use cases coordinate work. Repositories and provider adapters hide infrastructure. No route should call an LLM, Pinecone, or BIS source directly.

## Reliability and Security

Use environment-backed settings, secret redaction, timeouts, retries only for safe transient failures, idempotent ingestion, bounded uploads, structured logs, correlation IDs, and explicit provider failure states. Never log document contents or credentials by default. Store only permitted source-derived content and retain provenance.

## Authority and Uncertainty

The result model must support `verified`, `supported`, `inferred`, `unavailable`, `conflicting`, and `requires_verification` states. For example, if certification applicability cannot be established from current authoritative evidence, the UI must say that evidence is insufficient and direct verification against the latest official notification. It must not state that certification is mandatory.

## Deployment Shape

React is deployed as a frontend and FastAPI as a backend, using Neon PostgreSQL and Pinecone as managed services. PaddleOCR may run with the backend or a bounded worker later if measured workload requires it. Docker, Redis, Neo4j, translation APIs, and queues are deferred until a demonstrated requirement exists.

## Open Decisions Requiring Verification

- Permitted BIS access method, data licensing, robots restrictions, and metadata/content coverage.
- Official sources for QCO, CRS, Hallmarking, and certification applicability.
- Final LLM, embedding, language detection, and optional reranking models.
- Authentication, hosting, retention, and observability providers.
- Whether document storage is required and which files may legally be retained.
