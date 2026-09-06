import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from app.application.input import InputProcessingPipeline
from app.application.language_labels import language_display_name
from app.application.multilingual import MultilingualInput
from app.application.recommendation_details import RecommendationDetailsService, enrich_requirement
from app.application.requirement_mapping import build_requirement_mapping
from app.infrastructure.repositories.standards import StandardRepository
from app.settings import Settings


@dataclass(frozen=True)
class RecommendationResult:
    requirement: dict[str, Any]
    standards: list[dict[str, Any]]
    missing_information: list[str]
    tender_ready_recommendations: list[str]
    summary: dict[str, Any]
    document: dict[str, Any] | None = None


class RecommendationService:
    """Coordinate evidence-backed text recommendations with live BIS fallback capability."""

    def __init__(
        self,
        session: Any,
        input_pipeline: InputProcessingPipeline | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.session = session
        self.repository = StandardRepository(session)
        self.input_pipeline = input_pipeline or InputProcessingPipeline()
        self.settings = settings
        self.details = RecommendationDetailsService(self.repository, settings)

    async def recommend(
        self,
        text: str,
        language: str | None = None,
        *,
        refinement: str | None = None,
        document: dict[str, Any] | None = None,
    ) -> RecommendationResult:
        combined_text = _combine_requirement(text, refinement)
        extraction = await self.input_pipeline.process(MultilingualInput(original_text=combined_text, source="upload" if document else "recommendation"))
        terms = _terms(extraction.extracted_text)
        canonical_query = " ".join(terms)
        standard_count = await self.repository.count_standards()
        candidates = list(await self.repository.search_candidates(terms)) if standard_count else []
        live_source_used = False

        # If database is empty or no candidates matched, execute live official BIS fallback lookup
        if (standard_count == 0 or not candidates) and terms:
            try:
                from app.ingestion.adapters import BisMetadataAdapter
                from app.ingestion.service import IngestionService
                adapter = BisMetadataAdapter(queries=terms, max_records=20)
                stats = await IngestionService(self.session).ingest(adapter, mode="full")
                if stats.inserted > 0 or stats.updated > 0 or stats.skipped > 0:
                    live_source_used = True
                    standard_count = await self.repository.count_standards()
                    candidates = list(await self.repository.search_candidates(terms))
            except Exception:
                pass

        ranked = []
        for standard in candidates:
            score, factors = _score(standard, terms)
            if score <= 0:
                continue
            evidence_state = _evidence_state(standard)
            versions = sorted(standard.versions, key=lambda item: (item.is_current is True, item.edition_year or 0), reverse=True)
            current_version = next((item for item in versions if item.is_current is True), None)
            if current_version is None and len(versions) == 1:
                current_version = versions[0]
            relationships = []
            for relationship in (*standard.relationships_from, *standard.relationships_to):
                if relationship.source_record_id:
                    related = relationship.target_standard if relationship.source_standard_id == standard.id else relationship.source_standard
                    relationships.append({
                        "standard_id": related.id,
                        "is_number": related.is_number,
                        "title": related.title,
                        "relationship_type": relationship.relationship_type,
                        "evidence_note": relationship.evidence_note,
                        "source_record_id": relationship.source_record_id,
                    })
            compliance = await self.repository.compliance_for_standard(standard.id)
            mapping = build_requirement_mapping(combined_text, terms, standard, factors)
            ranked.append({
                "standard_id": standard.id,
                "is_number": standard.is_number,
                "title": standard.title,
                "standard_type": standard.standard_type,
                "status": standard.status,
                "relevance_score": round(score, 4),
                "applicability_status": "RELEVANT" if score >= 0.45 else "POSSIBLY_RELEVANT",
                "confidence": round(min(score + (0.2 if evidence_state != "requires_verification" else 0), 1), 4),
                "reasons": factors,
                "evidence_state": evidence_state,
                "provenance": _provenance(standard),
                "version": _version(current_version),
                "relationships": relationships,
                "compliance": compliance,
                "mapping": mapping,
            })
        ranked.sort(key=lambda item: (-item["relevance_score"], item["is_number"]))
        
        status = "database_empty" if standard_count == 0 else (
            "live_source_used" if (live_source_used and ranked) else (
                "recommendations_found" if ranked else "no_match"
            )
        )
        retrieval_method = "bis_live_metadata_lookup" if live_source_used else "postgresql_metadata_fallback"

        requirement = enrich_requirement({
            "original_text": text,
            "normalized_text": extraction.normalized_text,
            "combined_text": combined_text,
            "language": language or extraction.language.code,
            "detected_language": extraction.language.code,
            "detected_language_label": language_display_name(extraction.language.code),
            "technical_keywords": terms,
            "canonical_query": canonical_query,
        }, extraction.language.code)

        return RecommendationResult(
            requirement=requirement,
            standards=ranked,
            missing_information=_missing_information(extraction.normalized_text),
            tender_ready_recommendations=[
                "Use only standards marked RELEVANT after procurement review.",
                "Verify current editions, amendments, and compliance notifications against official sources.",
            ] if ranked else [
                "Data blocker: no standards are currently stored in PostgreSQL. Load an authorized standards dataset before making recommendations."
                if standard_count == 0 else
                "No relevant standards matched the supplied requirement. Verify the requirement terms or expand the authorized dataset."
            ],
            summary={
                "status": status,
                "standards_in_database": standard_count,
                "candidates_retrieved": len(candidates),
                "recommendations_returned": len(ranked),
                "retrieval_method": retrieval_method,
                "canonical_query": canonical_query,
            },
            document=document,
        )

    async def refine(self, original_text: str, refinement: str, language: str | None = None) -> RecommendationResult:
        if not refinement.strip():
            raise ValueError("Refinement text is required")
        return await self.recommend(original_text, language, refinement=refinement)



_MULTILINGUAL_DICTIONARY: dict[str, str] = {
    # ── Malayalam ────────────────────────────────────────────────────────────
    "കോൺക്രീറ്റ്": "concrete",
    "ബലപ്പെടുത്തുന്നതിനുള്ള": "reinforcement",
    "ഉയർന്ന": "high",
    "കരുത്തുള്ള": "strength",
    "ഡിഫോംഡ്": "deformed",
    "സ്റ്റീൽ": "steel",
    "ബാറുകൾ": "bars",
    "കമ്പികൾ": "rebars bars",
    "നിർമ്മാണം": "construction",
    "കെട്ടിടം": "building construction",
    "കുടിവെള്ള": "drinking water",
    "വെള്ളം": "water",
    "ഗുണനിലവാരം": "quality",
    "എയർ": "air",
    "കണ്ടീഷണർ": "conditioner",
    "വൈദ്യുതി": "electrical",
    "കേബിൾ": "cable",
    "വയർ": "wire",
    "പൈപ്പ്": "pipe",
    "പൈപ്പുകൾ": "pipes",
    # hot-rolled structural steel (Malayalam)
    "ഹോട്ട്": "hot",
    "റോൾഡ്": "rolled",
    "മീഡിയം": "medium",
    "ഹൈ": "high",
    "ടെൻസൈൽ": "tensile",
    "സ്ട്രക്ചറൽ": "structural",
    # stainless steel pipe (Malayalam)
    "സ്റ്റെയിൻലെസ്": "stainless",
    # ── Hindi ────────────────────────────────────────────────────────────────
    "कंक्रीट": "concrete",
    "सुदृढीकरण": "reinforcement",
    "उच्च": "high",
    "सामर्थ्य": "strength",
    "स्टील": "steel",
    "छड़": "bars",
    "निर्माण": "construction",
    "पेयजल": "drinking water",
    "पानी": "water",
    "गुणवत्ता": "quality",
    "एयर": "air",
    "कंडीशनर": "conditioner",
    "बिजली": "electrical",
    "तार": "wire",
    "केबल": "cable",
    "पाइप": "pipe",
    # hot-rolled structural steel (Hindi)
    "हॉट": "hot",
    "रोल्ड": "rolled",
    "मीडियम": "medium",
    "और": "and",
    "हाई": "high",
    "टेन्साइल": "tensile",
    "स्ट्रक्चरल": "structural",
    # stainless steel pipe (Hindi)
    "स्टेनलेस": "stainless",
    # ── Tamil ────────────────────────────────────────────────────────────────
    "காங்கிரீட்": "concrete",
    "எஃகு": "steel",
    "கம்பிகள்": "bars",
    "உயர்": "high",
    "வலிமை": "strength",
    "கட்டுமானம்": "construction",
    "குடிநீர்": "drinking water",
    "நீர்": "water",
    "ஏர்": "air",
    "கண்டிஷனர்": "conditioner",
    "மின்சார": "electrical",
    "கம்பி": "wire",
    "குழாய்": "pipe",
    # hot-rolled structural steel (Tamil)
    "சூடான": "hot",
    "உருட்டப்பட்ட": "rolled",
    "நடுத்தர": "medium",
    "மற்றும்": "and",
    "அதிக": "high",
    "இழுவிசை": "tensile",
    "கட்டமைப்பு": "structural",
    # stainless steel pipe (Tamil)
    "துருப்பிடிக்காத": "stainless",
}


_FUNCTION_WORDS = frozenset({
    "and", "or", "of", "the", "for", "to", "in", "a", "an", "with", "by", "on", "from",
})
_DICTIONARY = {unicodedata.normalize("NFC", key.casefold()): value for key, value in _MULTILINGUAL_DICTIONARY.items()}


def _combine_requirement(original_text: str, refinement: str | None) -> str:
    if not refinement or not refinement.strip():
        return original_text.strip()
    return f"{original_text.strip()}\n\nAdditional requirement details:\n{refinement.strip()}"


def _terms(text: str) -> list[str]:
    """Extract canonical English search terms from any supported language.

    Strategy:
    1. Split the input on whitespace to preserve multi-codepoint Indic words
       (Python's re.findall breaks Devanagari/Malayalam into sub-codepoints).
    2. For each token:
       - If it is pure ASCII (Latin script), keep it as-is — it is already an
         English technical term.
       - If it exists in _MULTILINGUAL_DICTIONARY, replace it with its English
         translation(s).
       - Otherwise drop it — untranslatable Indic tokens must NOT inflate the
         denominator of the relevance score.
    3. Also run regex tokenisation on the original text to capture IS-number
         fragments and hyphenated terms, keeping only ASCII results.
    4. Drop language-neutral function words so they cannot change ranking.
    """
    canonical: list[str] = []

    def _is_ascii(s: str) -> bool:
        return all(ord(c) < 128 for c in s)

    normalized = unicodedata.normalize("NFC", text)

    for raw in normalized.split():
        token = unicodedata.normalize("NFC", raw.strip(".,;:!?()[]{}'\"").casefold())
        if not token or len(token) < 2:
            continue
        if _is_ascii(token):
            if token not in canonical:
                canonical.append(token)
        elif token in _DICTIONARY:
            for eng in _DICTIONARY[token].split():
                if eng not in canonical:
                    canonical.append(eng)

    for token in re.findall(r"[\w-]+", normalized.casefold()):
        if len(token) >= 2 and _is_ascii(token) and token not in canonical:
            canonical.append(token)

    content = [term for term in canonical if term not in _FUNCTION_WORDS]
    return content or canonical




def _score(standard: Any, terms: list[str]) -> tuple[float, list[str]]:
    searchable = " ".join((standard.is_number, standard.title, standard.standard_type or "")).casefold()
    matches = [term for term in terms if term in searchable]
    if not matches:
        return 0, []
    score = min(0.9, 0.25 + (0.65 * len(matches) / max(len(terms), 1)))
    factors = [f"Matched keyword: {term}" for term in matches[:6]]
    return score, factors


def _evidence_state(standard: Any) -> str:
    if standard.source_record is None:
        return "requires_verification"
    return "supported" if standard.source_record.source_status in {"retrieved", "verified", "active"} else "requires_verification"


def _provenance(standard: Any) -> dict[str, Any]:
    source = standard.source_record
    return {
        "source_record_id": standard.source_record_id,
        "source_url": source.source_url if source else None,
        "source_type": source.source_type if source else None,
        "retrieved_at": source.retrieved_at.isoformat() if source and source.retrieved_at else None,
    }


def _version(current: Any) -> dict[str, Any]:
    if current is None:
        return {"status": "current_version_unverified", "message": "Current version could not be verified from available source data.", "edition_label": None, "amendments": []}
    return {
        "status": "current" if current.is_current is True else "unverified",
        "message": None if current.is_current is True else "Current version could not be verified from available source data.",
        "edition_label": current.edition_label,
        "edition_year": current.edition_year,
        "amendments": [{"label": amendment.amendment_label, "title": amendment.title, "publication_date": amendment.publication_date.isoformat() if amendment.publication_date else None} for amendment in current.amendments],
    }


def _missing_information(text: str) -> list[str]:
    missing = []
    if not re.search(r"\b(mm|cm|m|kg|kn|mpa|v|a)\b|\d", text.casefold()):
        missing.append("Dimensions or performance values")
    if not any(term in text.casefold() for term in ("indoor", "outdoor", "industrial", "residential")):
        missing.append("Intended installation environment")
    return missing
