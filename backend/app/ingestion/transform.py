import re
from datetime import date, datetime
from typing import Any

from app.ingestion.contracts import (
    AmendmentInput,
    CertificationInput,
    ClassificationInput,
    RawSourceRecord,
    RegulatoryInput,
    RelationshipInput,
    StandardIngestionRecord,
    VersionInput,
)

ALLOWED_RELATIONSHIP_TYPES = {"REFERRED", "NORMATIVE", "TEST_METHOD", "TERMINOLOGY", "SAFETY", "INSTALLATION", "ALLIED", "SUPERSEDES", "SUPERSEDED_BY", "RELATED"}
ALLOWED_STATUS = {"unknown", "active", "current", "superseded", "withdrawn", "draft", "test-only"}


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", str(value)).strip()
    return cleaned or None


def parse_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    raw = str(value).strip()
    for pattern in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, pattern).date()
        except ValueError:
            continue
    raise ValueError(f"Unsupported date format: {raw}")


def normalize_is_number(value: Any) -> str | None:
    cleaned = clean_text(value)
    return re.sub(r"\s*:\s*", " : ", cleaned).upper() if cleaned else None


def normalize_status(value: Any) -> str:
    status = (clean_text(value) or "unknown").lower().replace(" ", "_")
    aliases = {"active/current": "current", "active": "active", "superseded/withdrawn": "superseded"}
    return aliases.get(status, status)


def parse_standard(raw: RawSourceRecord) -> StandardIngestionRecord:
    payload = raw.payload
    versions = tuple(
        VersionInput(
            edition_label=clean_text(item.get("edition_label")) or "unknown",
            edition_year=int(item["edition_year"]) if item.get("edition_year") not in (None, "") else None,
            publication_date=parse_date(item.get("publication_date")),
            is_current=item.get("is_current"),
            status=normalize_status(item.get("status")),
            source_identifier=clean_text(item.get("source_identifier")),
        )
        for item in payload.get("versions", [])
    )
    amendments_by_edition: dict[str, tuple[AmendmentInput, ...]] = {}
    for item in payload.get("amendments", []):
        edition = clean_text(item.get("edition_label")) or "unknown"
        amendments_by_edition.setdefault(edition, ())
        amendments_by_edition[edition] += (AmendmentInput(
            amendment_label=clean_text(item.get("amendment_label")) or "unknown",
            title=clean_text(item.get("title")),
            publication_date=parse_date(item.get("publication_date")),
            details=clean_text(item.get("details")),
            source_identifier=clean_text(item.get("source_identifier")),
        ),)
    return StandardIngestionRecord(
        source=raw,
        is_number=normalize_is_number(payload.get("is_number")) or "",
        title=clean_text(payload.get("title")) or "",
        standard_type=clean_text(payload.get("standard_type")),
        publication_info=clean_text(payload.get("publication_info")),
        review_info=clean_text(payload.get("review_info")),
        technical_committee=clean_text(payload.get("technical_committee")),
        status=normalize_status(payload.get("status")),
        versions=versions,
        amendments_by_edition=amendments_by_edition,
        classifications=tuple(ClassificationInput(scheme=clean_text(item.get("scheme")) or "", code=clean_text(item.get("code")) or "", title=clean_text(item.get("title")) or "", description=clean_text(item.get("description"))) for item in payload.get("classifications", [])),
        relationships=tuple(RelationshipInput(target_is_number=normalize_is_number(item.get("target_is_number")) or "", relationship_type=(clean_text(item.get("relationship_type")) or "").upper(), evidence_note=clean_text(item.get("evidence_note")), source_identifier=clean_text(item.get("source_identifier"))) for item in payload.get("relationships", [])),
        certifications=tuple(CertificationInput(scheme_name=clean_text(item.get("scheme_name")) or "", external_identifier=clean_text(item.get("external_identifier")) or "", title=clean_text(item.get("title")) or "", applicability_note=clean_text(item.get("applicability_note")), source_identifier=clean_text(item.get("source_identifier"))) for item in payload.get("certifications", [])),
        qco_records=tuple(_regulatory(item) for item in payload.get("qco_records", [])),
        crs_records=tuple(_regulatory(item) for item in payload.get("crs_records", [])),
        hallmarking_rules=tuple(_regulatory(item) for item in payload.get("hallmarking_rules", [])),
    )


def _regulatory(item: dict[str, Any]) -> RegulatoryInput:
    return RegulatoryInput(identifier=clean_text(item.get("identifier")) or "", title=clean_text(item.get("title")) or "", applicability_note=clean_text(item.get("applicability_note")), effective_from=parse_date(item.get("effective_from")), effective_to=parse_date(item.get("effective_to")), source_identifier=clean_text(item.get("source_identifier")))


def validate_standard(record: StandardIngestionRecord) -> list[str]:
    errors: list[str] = []
    if not record.source.source_type.strip(): errors.append("source_type is required")
    if not record.source.source_url.strip(): errors.append("source_url is required")
    if not record.source.external_identifier.strip(): errors.append("external_identifier is required")
    if not record.is_number: errors.append("is_number is required")
    if not record.title: errors.append("title is required")
    if record.status not in ALLOWED_STATUS: errors.append(f"unsupported status: {record.status}")
    for relationship in record.relationships:
        if not relationship.target_is_number: errors.append("relationship target_is_number is required")
        if relationship.relationship_type not in ALLOWED_RELATIONSHIP_TYPES: errors.append(f"unsupported relationship type: {relationship.relationship_type}")
        if relationship.target_is_number == record.is_number: errors.append("self-referential relationship is not allowed")
    for classification in record.classifications:
        if not classification.scheme or not classification.code or not classification.title: errors.append("classification scheme, code, and title are required")
    return errors
