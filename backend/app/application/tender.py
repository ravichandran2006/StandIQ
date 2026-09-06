from typing import Any


NOT_SPECIFIED = "Not specified in available authoritative source."
VERIFICATION_NOTE = (
    "AI-assisted draft generated from verified StandIQ metadata. "
    "Verify all clauses, editions, and compliance notifications against official BIS sources before tender publication."
)


def generate_tender_specification(requirement: dict[str, Any], standards: list[dict[str, Any]]) -> dict[str, Any]:
    if not standards:
        return {
            "status": "no_data",
            "message": "No recommended standards are available to generate a tender specification.",
            "specification": "",
            "disclaimer": VERIFICATION_NOTE,
            "sections": [],
        }

    sections: list[dict[str, str]] = []
    lines: list[str] = [
        "TENDER SPECIFICATION DRAFT",
        "",
        "1. Product Description",
        requirement.get("original_text") or NOT_SPECIFIED,
        "",
    ]
    sections.append({"title": "Product Description", "content": requirement.get("original_text") or NOT_SPECIFIED})

    for index, standard in enumerate(standards[:5], start=2):
        version = standard.get("version") or {}
        amendments = version.get("amendments") or []
        amendment_text = "; ".join(
            f"{item.get('label')}: {item.get('title')}" for item in amendments
        ) if amendments else NOT_SPECIFIED
        block = [
            f"{index}. Applicable Indian Standard",
            f"Standard number: {standard.get('is_number') or NOT_SPECIFIED}",
            f"Title: {standard.get('title') or NOT_SPECIFIED}",
            f"Current version: {version.get('edition_label') or NOT_SPECIFIED}",
            f"Amendments: {amendment_text}",
            f"Technical requirements: Refer to scope and clauses of {standard.get('is_number') or 'the cited standard'}",
            f"Testing: {NOT_SPECIFIED}",
            f"Inspection: {NOT_SPECIFIED}",
        ]
        compliance = standard.get("compliance") or []
        if compliance:
            block.append("Certification / compliance:")
            for item in compliance:
                block.append(f"- {item.get('type')}: {item.get('title')} ({item.get('status')})")
        else:
            block.append(f"Certification / compliance: {NOT_SPECIFIED}")
        provenance = standard.get("provenance") or {}
        block.append(f"Source / evidence: {provenance.get('source_url') or NOT_SPECIFIED}")
        lines.extend(block)
        lines.append("")
        sections.append({"title": f"Standard {standard.get('is_number')}", "content": "\n".join(block)})

    lines.extend([
        "Acceptance Criteria",
        "Materials shall conform to the cited Indian Standard edition and applicable amendments verified at tender stage.",
        "",
        "Required Documentation",
        "Manufacturer test certificates, BIS license / compliance documents where applicable, and source traceability records.",
        "",
        VERIFICATION_NOTE,
    ])
    sections.append({"title": "Acceptance Criteria", "content": lines[-6]})
    sections.append({"title": "Required Documentation", "content": lines[-4]})

    return {
        "status": "success",
        "message": None,
        "specification": "\n".join(lines),
        "disclaimer": VERIFICATION_NOTE,
        "sections": sections,
    }
