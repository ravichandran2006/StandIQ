from typing import Any

import httpx

from app.settings import Settings


class LLMUnavailableError(Exception):
    pass


def _configuration_error(settings: Settings) -> str:
    """Return a specific message identifying which config field is missing."""
    missing = []
    if not settings.llm_provider:
        missing.append("LLM_PROVIDER")
    if not settings.llm_api_key or not settings.llm_api_key.get_secret_value().strip():
        missing.append("LLM_API_KEY")
    if not settings.llm_model:
        missing.append("LLM_MODEL")
    if missing:
        return f"LLM is not configured. Missing: {', '.join(missing)}."
    return "LLM is not configured."


async def generate_text(settings: Settings, *, system_prompt: str, user_prompt: str) -> str:
    if not settings.llm_configured():
        raise LLMUnavailableError(_configuration_error(settings))

    provider = (settings.llm_provider or "").lower()
    api_key = settings.llm_api_key.get_secret_value()  # type: ignore[union-attr]
    model = settings.llm_model or ""

    if provider in {"openai", "openai-compatible"}:
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return str(data["choices"][0]["message"]["content"]).strip()

    if provider == "groq":
        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 1024,
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return str(data["choices"][0]["message"]["content"]).strip()

    if provider == "together":
        url = "https://api.together.xyz/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return str(data["choices"][0]["message"]["content"]).strip()

    if provider in {"gemini", "google"}:
        # Google Generative Language API (Gemini)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1024},
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return str(data["candidates"][0]["content"]["parts"][0]["text"]).strip()

    raise LLMUnavailableError(
        f"Unsupported LLM provider: '{settings.llm_provider}'. "
        "Supported providers: groq, openai, openai-compatible, together, gemini, google."
    )


def build_explanation_context(payload: dict[str, Any]) -> str:
    language = payload.get("detected_language") or "en"
    language_label = payload.get("detected_language_label") or "English"
    lines = [
        "Verified recommendation context (do not add standards, amendments, or compliance rules beyond this list):",
        f"Requirement: {payload.get('original_text', '')}",
        f"Normalized requirement: {payload.get('normalized_text', '')}",
        f"Detected language: {language_label} ({language})",
        f"Canonical search terms: {', '.join(payload.get('technical_keywords', []))}",
    ]
    standard = payload.get("standard") or {}
    lines.extend([
        f"Recommended standard: {standard.get('is_number')} — {standard.get('title')}",
        f"Standard type: {standard.get('standard_type') or 'Not specified'}",
        f"Status: {standard.get('status') or 'Not specified'}",
        f"Applicability: {standard.get('applicability_status')} (score {standard.get('relevance_score')})",
        f"Evidence state: {standard.get('evidence_state')}",
        "Applicability signals:",
        *[f"- {reason}" for reason in standard.get("reasons", [])],
    ])
    version = standard.get("version") or {}
    if version.get("edition_label"):
        lines.append(f"Current edition: {version.get('edition_label')} ({version.get('edition_year')})")
    amendments = version.get("amendments") or []
    if amendments:
        lines.append("Amendments:")
        for amendment in amendments:
            lines.append(f"- {amendment.get('label')}: {amendment.get('title')}")
    relationships = standard.get("relationships") or []
    if relationships:
        lines.append("Stored relationships:")
        for rel in relationships[:8]:
            lines.append(f"- {rel.get('relationship_type')}: {rel.get('is_number')} — {rel.get('title')}")
    compliance = standard.get("compliance") or []
    if compliance:
        lines.append("Stored compliance records:")
        for item in compliance:
            lines.append(f"- {item.get('type')}: {item.get('title')} ({item.get('status')})")
    provenance = standard.get("provenance") or {}
    if provenance.get("source_url"):
        lines.append(f"Source URL: {provenance.get('source_url')}")
    return "\n".join(lines)


def _language_instruction(language: str | None) -> str:
    """Return instruction to respond in the user's language when applicable."""
    label_map = {"hi": "Hindi (हिन्दी)", "ta": "Tamil (தமிழ்)", "ml": "Malayalam (മലയാളം)"}
    label = label_map.get(language or "en")
    if label:
        return f" Respond in {label} if the requirement is in that language, otherwise respond in English."
    return ""


EXPLANATION_SYSTEM_PROMPT = (
    "You explain why an Indian Standard was recommended for a procurement requirement. "
    "Use ONLY the verified context provided. Do NOT invent IS numbers, titles, amendments, "
    "relationships, certification requirements, or QCO applicability. "
    "If information is missing, say it is not available in the supplied evidence. "
    "Structure your explanation with: (1) What the requirement means, "
    "(2) Why this standard is applicable, (3) Key matching attributes, "
    "(4) Evidence and limitations."
)


def deterministic_explanation(payload: dict[str, Any]) -> str:
    standard = payload.get("standard") or {}
    reasons = standard.get("reasons") or []
    lines = [
        "This recommendation is based on verified metadata and applicability signals already stored in StandIQ.",
        f"The requirement was matched to {standard.get('is_number')} — {standard.get('title')}.",
    ]
    if reasons:
        lines.append("Supporting signals:")
        lines.extend(f"- {reason}" for reason in reasons)
    else:
        lines.append("No keyword overlap signals were recorded for this match.")
    evidence = standard.get("evidence_state")
    if evidence:
        lines.append(f"Evidence state: {evidence}.")
    return "\n".join(lines)
