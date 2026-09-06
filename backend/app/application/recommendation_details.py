from typing import Any

from app.application.language_labels import language_display_name
from app.application.llm import (
    EXPLANATION_SYSTEM_PROMPT,
    LLMUnavailableError,
    build_explanation_context,
    deterministic_explanation,
    generate_text,
)
from app.application.requirement_mapping import build_requirement_mapping
from app.application.tender import generate_tender_specification
from app.infrastructure.repositories.standards import StandardRepository
from app.settings import Settings


SUPPORTED_RELATIONSHIP_TYPES = frozenset({
    "REFERRED", "NORMATIVE", "TEST_METHOD", "TERMINOLOGY", "SAFETY",
    "INSTALLATION", "ALLIED", "SUPERSEDES", "SUPERSEDED_BY", "RELATED",
})


class RecommendationDetailsService:
    def __init__(self, repository: StandardRepository, settings: Settings | None = None) -> None:
        self.repository = repository
        self.settings = settings

    async def related_standards(self, standard_id: str) -> dict[str, Any]:
        standard = await self.repository.get_by_id(standard_id)
        if standard is None:
            return {"status": "not_found", "message": "Standard not found.", "items": []}

        rows: list[dict[str, Any]] = []
        for relationship in (*standard.relationships_from, *standard.relationships_to):
            if relationship.relationship_type not in SUPPORTED_RELATIONSHIP_TYPES:
                continue
            related = relationship.target_standard if relationship.source_standard_id == standard.id else relationship.source_standard
            rows.append({
                "standard": related.is_number,
                "title": related.title,
                "relationship": relationship.relationship_type,
                "why_relevant": relationship.evidence_note or "Relationship recorded in authoritative source metadata.",
                "status": related.status,
                "standard_id": related.id,
            })
        if not rows:
            return {"status": "no_data", "message": "No related or normative standards are recorded for this standard.", "items": []}
        return {"status": "success", "message": None, "items": rows}

    async def version_history(self, standard_id: str) -> dict[str, Any]:
        standard = await self.repository.get_by_id(standard_id)
        if standard is None:
            return {"status": "not_found", "message": "Standard not found.", "items": []}

        versions = sorted(
            standard.versions,
            key=lambda item: (item.edition_year or 0, item.edition_label),
            reverse=True,
        )
        superseding = [
            rel.target_standard.is_number
            for rel in standard.relationships_from
            if rel.relationship_type in {"SUPERSEDES"} and rel.target_standard is not None
        ]
        superseded_by = [
            *(rel.source_standard.is_number for rel in standard.relationships_to if rel.relationship_type == "SUPERSEDES" and rel.source_standard is not None),
            *(rel.target_standard.is_number for rel in standard.relationships_from if rel.relationship_type == "SUPERSEDED_BY" and rel.target_standard is not None),
        ]

        if not versions and not superseding and not superseded_by:
            return {
                "status": "no_data",
                "message": "No version history is available for this standard.",
                "items": [],
            }

        items: list[dict[str, Any]] = []
        for version in versions:
            source = version.source_record
            items.append({
                "standard_number": standard.is_number,
                "version": version.edition_label,
                "year": version.edition_year,
                "status": version.status,
                "publication_info": standard.publication_info,
                "review_info": standard.review_info,
                "amendments": [
                    {
                        "label": amendment.amendment_label,
                        "title": amendment.title,
                        "publication_date": amendment.publication_date.isoformat() if amendment.publication_date else None,
                    }
                    for amendment in version.amendments
                ],
                "superseding_standard": ", ".join(superseding) if superseding else None,
                "superseded_by": ", ".join(superseded_by) if superseded_by else None,
                "source_url": source.source_url if source else None,
            })
        return {"status": "success", "message": None, "items": items}

    async def compliance_details(self, standard_id: str) -> dict[str, Any]:
        standard = await self.repository.get_by_id(standard_id)
        if standard is None:
            return {"status": "not_found", "message": "Standard not found.", "items": []}

        details = await self.repository.compliance_details_for_standard(standard_id)
        if not any(details.values()):
            return {
                "status": "no_data",
                "message": "Authoritative compliance information is not available for this requirement.",
                "items": [],
            }
        return {"status": "success", "message": None, "items": details}

    async def requirement_mapping(self, standard_id: str, text: str, terms: list[str], reasons: list[str]) -> dict[str, Any]:
        standard = await self.repository.get_by_id(standard_id)
        if standard is None:
            return {"status": "not_found", "message": "Standard not found.", "items": []}
        rows = build_requirement_mapping(text, terms, standard, reasons)
        return {"status": "success", "message": None, "items": rows}

    async def source_documents(self, standard_id: str) -> dict[str, Any]:
        standard = await self.repository.get_by_id(standard_id)
        if standard is None:
            return {"status": "not_found", "message": "Standard not found.", "items": []}
        items = await self.repository.source_records_for_standard(standard_id)
        if not items:
            return {"status": "no_data", "message": "No source documents are recorded for this standard.", "items": []}
        return {"status": "success", "message": None, "items": items}

    async def all_evidence(self, standard_id: str, text: str, terms: list[str], reasons: list[str]) -> dict[str, Any]:
        standard = await self.repository.get_by_id(standard_id)
        if standard is None:
            return {"status": "not_found", "message": "Standard not found.", "items": []}
        items = await self.repository.evidence_bundle_for_standard(standard_id, text, terms, reasons)
        if not items:
            return {"status": "no_data", "message": "No evidence records are available.", "items": []}
        return {"status": "success", "message": None, "items": items}

    async def explanation(self, payload: dict[str, Any]) -> dict[str, Any]:
        fallback = deterministic_explanation(payload)
        if self.settings is None or not self.settings.llm_configured():
            from app.application.llm import _configuration_error
            msg = _configuration_error(self.settings) if self.settings else "LLM is not configured."
            return {
                "status": "unavailable",
                "message": msg,
                "explanation": fallback,
                "source": "deterministic",
            }
        try:
            explanation = await generate_text(
                self.settings,
                system_prompt=EXPLANATION_SYSTEM_PROMPT,
                user_prompt=build_explanation_context(payload),
            )
            return {"status": "success", "message": None, "explanation": explanation, "source": "llm"}
        except (LLMUnavailableError, Exception) as exc:
            return {
                "status": "backend_error",
                "message": str(exc),
                "explanation": fallback,
                "source": "deterministic",
            }

    async def tender(self, requirement: dict[str, Any], standards: list[dict[str, Any]]) -> dict[str, Any]:
        return generate_tender_specification(requirement, standards)


def enrich_requirement(requirement: dict[str, Any], extraction_language_code: str) -> dict[str, Any]:
    code = requirement.get("detected_language") or extraction_language_code
    requirement["detected_language_label"] = language_display_name(code)
    return requirement
