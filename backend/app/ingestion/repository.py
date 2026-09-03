from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Amendment, Certification, Classification, CrsMapping, CrsRecord, HallmarkingRule, IngestionRun, QcoMapping, QcoRecord, SourceRecord, Standard, StandardClassification, StandardRelationship, StandardVersion
from app.ingestion.contracts import CertificationInput, ClassificationInput, RegulatoryInput, RelationshipInput, StandardIngestionRecord, VersionInput, AmendmentInput


class IngestionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def begin_run(self, source_name: str) -> IngestionRun:
        run = IngestionRun(source_name=source_name, started_at=datetime.now(timezone.utc), status="running")
        self.session.add(run)
        await self.session.flush()
        return run

    async def finish_run(self, run: IngestionRun, status: str, stats: dict[str, Any]) -> None:
        run.completed_at = datetime.now(timezone.utc)
        run.status = status
        run.records_discovered = stats["discovered"]
        run.records_inserted = stats["inserted"]
        run.records_updated = stats["updated"]
        run.records_skipped = stats["skipped"]
        run.records_failed = stats["failed"]
        run.error_summary = "\n".join(stats["errors"]) or None
        await self.session.flush()

    async def upsert_source(self, record: StandardIngestionRecord, run_id: str) -> tuple[SourceRecord, bool]:
        source = (await self.session.execute(select(SourceRecord).where(SourceRecord.source_type == record.source.source_type, SourceRecord.external_identifier == record.source.external_identifier))).scalar_one_or_none()
        created = source is None
        if source is None:
            source = SourceRecord(source_type=record.source.source_type, external_identifier=record.source.external_identifier)
            self.session.add(source)
        source.source_url = record.source.source_url
        source.retrieved_at = record.source.retrieved_at
        source.last_checked_at = record.source.retrieved_at
        source.source_status = "retrieved"
        source.ingestion_run_id = run_id
        await self.session.flush()
        return source, created

    async def get_standard(self, is_number: str) -> Standard | None:
        return (await self.session.execute(select(Standard).where(Standard.is_number == is_number))).scalar_one_or_none()

    async def upsert_standard(self, record: StandardIngestionRecord, source: SourceRecord) -> tuple[Standard, bool, bool]:
        standard = await self.get_standard(record.is_number)
        created = standard is None
        changed = created
        if standard is None:
            standard = Standard(is_number=record.is_number, title=record.title, source_record=source)
            self.session.add(standard)
        fields = {"title": record.title, "standard_type": record.standard_type, "publication_info": record.publication_info, "review_info": record.review_info, "technical_committee": record.technical_committee, "status": record.status, "source_record": source}
        for field, value in fields.items():
            if getattr(standard, field) != value:
                setattr(standard, field, value)
                changed = True
        await self.session.flush()
        return standard, created, changed

    async def upsert_version(self, standard: Standard, item: VersionInput, source: SourceRecord) -> tuple[StandardVersion, bool]:
        statement = select(StandardVersion).where(StandardVersion.standard_id == standard.id)
        if item.edition_year is not None:
            statement = statement.where(StandardVersion.edition_year == item.edition_year)
        else:
            statement = statement.where(StandardVersion.edition_label == item.edition_label)
        version = (await self.session.execute(statement)).scalar_one_or_none()
        created = version is None
        if version is None:
            version = StandardVersion(standard=standard, edition_label=item.edition_label, edition_year=item.edition_year)
            self.session.add(version)
        version.edition_label = item.edition_label
        version.publication_date = item.publication_date
        version.is_current = item.is_current
        version.status = item.status
        version.source_record = source
        await self.session.flush()
        return version, created

    async def upsert_amendment(self, version: StandardVersion, item: AmendmentInput, source: SourceRecord) -> bool:
        amendment = (await self.session.execute(select(Amendment).where(Amendment.standard_version_id == version.id, Amendment.amendment_label == item.amendment_label))).scalar_one_or_none()
        created = amendment is None
        if amendment is None:
            amendment = Amendment(standard_version=version, amendment_label=item.amendment_label)
            self.session.add(amendment)
        amendment.title = item.title
        amendment.publication_date = item.publication_date
        amendment.details = item.details
        amendment.source_record = source
        await self.session.flush()
        return created

    async def upsert_classification(self, standard: Standard, item: ClassificationInput) -> bool:
        classification = (await self.session.execute(select(Classification).where(Classification.scheme == item.scheme, Classification.code == item.code))).scalar_one_or_none()
        created = classification is None
        if classification is None:
            classification = Classification(scheme=item.scheme, code=item.code, title=item.title, description=item.description)
            self.session.add(classification)
            await self.session.flush()
        link = (await self.session.execute(select(StandardClassification).where(StandardClassification.standard_id == standard.id, StandardClassification.classification_id == classification.id))).scalar_one_or_none()
        if link is None:
            self.session.add(StandardClassification(standard=standard, classification=classification))
            await self.session.flush()
        return created

    async def upsert_relationship(self, standard: Standard, item: RelationshipInput, source: SourceRecord) -> tuple[bool, bool]:
        target = await self.get_standard(item.target_is_number)
        if target is None:
            return False, False
        relationship = (await self.session.execute(select(StandardRelationship).where(StandardRelationship.source_standard_id == standard.id, StandardRelationship.target_standard_id == target.id, StandardRelationship.relationship_type == item.relationship_type))).scalar_one_or_none()
        created = relationship is None
        if relationship is None:
            relationship = StandardRelationship(source_standard=standard, target_standard=target, relationship_type=item.relationship_type)
            self.session.add(relationship)
        relationship.evidence_note = item.evidence_note
        relationship.source_record = source
        await self.session.flush()
        return created, True

    async def upsert_certification(self, item: CertificationInput, source: SourceRecord) -> bool:
        record = (await self.session.execute(select(Certification).where(Certification.scheme_name == item.scheme_name, Certification.external_identifier == item.external_identifier))).scalar_one_or_none()
        created = record is None
        if record is None:
            record = Certification(scheme_name=item.scheme_name, external_identifier=item.external_identifier, title=item.title)
            self.session.add(record)
        record.title = item.title
        record.applicability_note = item.applicability_note
        record.source_record = source
        await self.session.flush()
        return created

    async def upsert_regulatory(self, standard: Standard, item: RegulatoryInput, source: SourceRecord, kind: str) -> bool:
        model = {"qco": QcoRecord, "crs": CrsRecord, "hallmarking": HallmarkingRule}[kind]
        field = {"qco": "notification_number", "crs": "registration_number", "hallmarking": "rule_identifier"}[kind]
        record = (await self.session.execute(select(model).where(getattr(model, field) == item.identifier))).scalar_one_or_none()
        created = record is None
        if record is None:
            record = model(**{field: item.identifier, "title": item.title})
            self.session.add(record)
        record.title = item.title
        record.applicability_note = item.applicability_note
        if kind != "hallmarking":
            record.effective_from = item.effective_from
            record.effective_to = item.effective_to
        record.source_record = source
        await self.session.flush()
        if kind == "qco":
            exists = (await self.session.execute(select(QcoMapping).where(QcoMapping.qco_record_id == record.id, QcoMapping.standard_id == standard.id))).scalar_one_or_none()
            if exists is None: self.session.add(QcoMapping(qco_record=record, standard=standard))
        elif kind == "crs":
            exists = (await self.session.execute(select(CrsMapping).where(CrsMapping.crs_record_id == record.id, CrsMapping.standard_id == standard.id))).scalar_one_or_none()
            if exists is None: self.session.add(CrsMapping(crs_record=record, standard=standard))
        await self.session.flush()
        return created
