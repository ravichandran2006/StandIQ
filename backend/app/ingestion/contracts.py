from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Literal


@dataclass(frozen=True)
class RawSourceRecord:
    source_type: str
    source_url: str
    external_identifier: str
    payload: dict[str, Any]
    retrieved_at: datetime


@dataclass(frozen=True)
class VersionInput:
    edition_label: str
    edition_year: int | None = None
    publication_date: date | None = None
    is_current: bool | None = None
    status: str = "unknown"
    source_identifier: str | None = None


@dataclass(frozen=True)
class AmendmentInput:
    amendment_label: str
    title: str | None = None
    publication_date: date | None = None
    details: str | None = None
    source_identifier: str | None = None


@dataclass(frozen=True)
class ClassificationInput:
    scheme: str
    code: str
    title: str
    description: str | None = None


@dataclass(frozen=True)
class RelationshipInput:
    target_is_number: str
    relationship_type: str
    evidence_note: str | None = None
    source_identifier: str | None = None


@dataclass(frozen=True)
class CertificationInput:
    scheme_name: str
    external_identifier: str
    title: str
    applicability_note: str | None = None
    source_identifier: str | None = None


@dataclass(frozen=True)
class RegulatoryInput:
    identifier: str
    title: str
    applicability_note: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    source_identifier: str | None = None


@dataclass(frozen=True)
class StandardIngestionRecord:
    source: RawSourceRecord
    is_number: str
    title: str
    standard_type: str | None = None
    publication_info: str | None = None
    review_info: str | None = None
    technical_committee: str | None = None
    status: str = "unknown"
    versions: tuple[VersionInput, ...] = ()
    amendments_by_edition: dict[str, tuple[AmendmentInput, ...]] = field(default_factory=dict)
    classifications: tuple[ClassificationInput, ...] = ()
    relationships: tuple[RelationshipInput, ...] = ()
    certifications: tuple[CertificationInput, ...] = ()
    qco_records: tuple[RegulatoryInput, ...] = ()
    crs_records: tuple[RegulatoryInput, ...] = ()
    hallmarking_rules: tuple[RegulatoryInput, ...] = ()


@dataclass
class IngestionStats:
    discovered: int = 0
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)

    def fail(self, message: str) -> None:
        self.failed += 1
        self.errors.append(message)

    def as_dict(self) -> dict[str, Any]:
        return {
            "discovered": self.discovered,
            "inserted": self.inserted,
            "updated": self.updated,
            "skipped": self.skipped,
            "failed": self.failed,
            "errors": list(self.errors),
        }


IngestionMode = Literal["full", "incremental"]
