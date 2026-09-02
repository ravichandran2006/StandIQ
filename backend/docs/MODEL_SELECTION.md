# Model Selection

Status: candidates only. No model has been selected and no benchmark has been run.

## LLM candidates

Evaluate provider-independent adapters against a held-out procurement set. Candidates include OpenAI GPT-4.1/4.1-mini, Google Gemini 2.5 Flash/Pro, and suitable Groq-hosted open models. Selection criteria are structured extraction quality, multilingual behavior in Malayalam, Tamil, Hindi, and English, technical requirement understanding, reasoning, evidence adherence, latency, cost, API availability, rate limits, reliability, and data handling.

## Embedding candidates

Evaluate multilingual-e5-large, BGE-M3, and Cohere Embed Multilingual for cross-language semantic retrieval. Measure recall and ranking quality for Malayalam, Tamil, Hindi, and English requirements; also verify dimensions, context limits, licensing, provider availability, cost, latency, and Pinecone compatibility.

## OCR

PaddleOCR is the required candidate for the later OCR phase. Evaluate script coverage, scanned-PDF behavior, table handling, confidence output, accuracy, CPU requirements, and failure behavior.

## Language detection

Compare fastText lid.176, Lingua, and a model-based fallback on short, noisy procurement text in the required languages. Measure accuracy, confidence calibration, script ambiguity handling, latency, and deployment footprint.

## Optional reranking

Evaluate bge-reranker-v2-m3 or a hosted multilingual reranker only if retrieval benchmarks show a meaningful gain. Include relevance quality, latency, cost, licensing, and operational complexity in the decision.

No benchmark results or accuracy claims are made in Phase 1.
