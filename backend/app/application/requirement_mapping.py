import re
from typing import Any


_ELEMENT_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Product", ("product", "type", "item", "equipment", "component")),
    ("Material", ("steel", "concrete", "copper", "aluminium", "aluminum", "plastic", "pvc", "stainless", "iron", "metal", "wire", "cable", "pipe", "bar", "rebar")),
    ("Application", ("industrial", "residential", "commercial", "construction", "building", "electrical", "structural", "drinking", "water", "wiring", "installation")),
    ("Dimensions", ("mm", "cm", "meter", "metre", "diameter", "thickness", "width", "length", "size", "dimension")),
    ("Performance", ("strength", "tensile", "load", "capacity", "pressure", "voltage", "current", "mpa", "kn")),
    ("Safety", ("safety", "fire", "hazard", "protection", "insulation")),
    ("Durability", ("corrosion", "durability", "weather", "outdoor", "indoor", "galvanized", "coating")),
    ("Testing", ("test", "testing", "inspection", "sampling", "method")),
    ("Certification", ("certification", "certified", "isi", "bis", "compliance", "license", "marking")),
    ("Technical attributes", ("hot", "rolled", "medium", "high", "perforated", "deformed", "structural", "specification")),
)


def _searchable(standard: Any) -> str:
    return " ".join((standard.is_number, standard.title, standard.standard_type or "")).casefold()


def build_requirement_mapping(text: str, terms: list[str], standard: Any, reasons: list[str]) -> list[dict[str, str]]:
    searchable = _searchable(standard)
    rows: list[dict[str, str]] = []
    text_lower = text.casefold()
    term_set = {term.casefold() for term in terms}

    for element, keywords in _ELEMENT_PATTERNS:
        extracted_values: list[str] = []
        for keyword in keywords:
            if keyword in text_lower or keyword in term_set:
                extracted_values.append(keyword)
        extracted = ", ".join(dict.fromkeys(extracted_values)) if extracted_values else "Not identified"

        matched_keywords = [keyword for keyword in keywords if keyword in searchable or keyword in term_set]
        if matched_keywords:
            match = "matched"
            evidence = f"Standard metadata contains: {', '.join(matched_keywords[:4])}"
        elif extracted_values:
            match = "partially matched"
            evidence = reasons[0] if reasons else "Requirement term present; direct standard metadata match not established"
        elif any(keyword in text_lower for keyword in keywords[:3]):
            match = "ambiguous"
            evidence = "Requirement mentions related concepts but match is inconclusive"
        else:
            match = "missing"
            evidence = "Not specified in requirement or available standard metadata"

        rows.append({
            "requirement_element": element,
            "extracted_value": extracted,
            "recommended_standard": standard.is_number,
            "supporting_evidence": evidence,
            "match": match,
        })

    if re.search(r"\b\d", text_lower):
        numeric_match = "matched" if re.search(r"\b\d", searchable) else "partially matched"
        rows.append({
            "requirement_element": "Numeric specification",
            "extracted_value": "Numeric values present in requirement",
            "recommended_standard": standard.is_number,
            "supporting_evidence": "Numeric values detected in requirement text",
            "match": numeric_match,
        })

    return rows
