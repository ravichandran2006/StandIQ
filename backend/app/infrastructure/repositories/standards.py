from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import Amendment, Certification, CrsMapping, CrsRecord, HallmarkingRule, QcoMapping, QcoRecord, SourceRecord, Standard, StandardClassification, StandardRelationship, StandardVersion


class StandardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, standard_id: str) -> Standard | None:
        statement = (
            select(Standard)
            .options(
                selectinload(Standard.source_record),
                selectinload(Standard.versions).selectinload(StandardVersion.amendments).selectinload(Amendment.source_record),
                selectinload(Standard.versions).selectinload(StandardVersion.source_record),
                selectinload(Standard.relationships_from).selectinload(StandardRelationship.target_standard),
                selectinload(Standard.relationships_from).selectinload(StandardRelationship.source_record),
                selectinload(Standard.relationships_to).selectinload(StandardRelationship.source_standard),
                selectinload(Standard.relationships_to).selectinload(StandardRelationship.source_record),
            )
            .where(Standard.id == standard_id)
        )
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def count_standards(self) -> int:
        return int((await self.session.execute(select(func.count()).select_from(Standard))).scalar_one())

    async def get_by_is_number(self, is_number: str) -> Standard | None:
        result = await self.session.execute(select(Standard).where(Standard.is_number == is_number))
        return result.scalar_one_or_none()

    async def list(self, *, offset: int, limit: int, status: str | None = None, search: str | None = None) -> tuple[Sequence[Standard], int]:
        filters = []
        if status:
            filters.append(Standard.status == status)
        if search:
            filters.append(Standard.title.ilike(f"%{search}%"))
        statement = select(Standard).where(*filters).order_by(Standard.is_number).offset(offset).limit(limit)
        count_statement = select(func.count()).select_from(Standard).where(*filters)
        rows = (await self.session.execute(statement)).scalars().all()
        total = (await self.session.execute(count_statement)).scalar_one()
        return rows, total

    async def list_by_status(self, status: str) -> Sequence[Standard]:
        rows, _ = await self.list(offset=0, limit=100, status=status)
        return rows

    async def list_for_index(self, *, offset: int, limit: int) -> Sequence[Standard]:
        statement = (
            select(Standard)
            .options(
                selectinload(Standard.versions),
                selectinload(Standard.classifications).selectinload(StandardClassification.classification),
                selectinload(Standard.source_record),
            )
            .order_by(Standard.is_number)
            .offset(offset)
            .limit(limit)
        )
        return (await self.session.execute(statement)).scalars().unique().all()

    async def search_candidates(self, terms: Sequence[str], *, limit: int = 50) -> Sequence[Standard]:
        searchable = [term for term in terms if len(term) >= 2]
        if not searchable:
            return []
        filters = [field.ilike(f"%{term}%") for term in searchable for field in (Standard.is_number, Standard.title, Standard.standard_type)]
        statement = (
            select(Standard)
            .options(
                selectinload(Standard.source_record),
                selectinload(Standard.versions).selectinload(StandardVersion.source_record),
                selectinload(Standard.versions).selectinload(StandardVersion.amendments),
                selectinload(Standard.classifications).selectinload(StandardClassification.classification),
                selectinload(Standard.relationships_from).selectinload(StandardRelationship.target_standard),
                selectinload(Standard.relationships_from).selectinload(StandardRelationship.source_record),
                selectinload(Standard.relationships_to).selectinload(StandardRelationship.source_standard),
                selectinload(Standard.relationships_to).selectinload(StandardRelationship.source_record),
            )
            .where(or_(*filters))
            .order_by(Standard.is_number)
            .limit(limit)
        )
        return (await self.session.execute(statement)).scalars().unique().all()

    async def compliance_for_standard(self, standard_id: str) -> list[dict[str, object]]:
        details = await self.compliance_details_for_standard(standard_id)
        results: list[dict[str, object]] = []
        for key in ("qco", "crs"):
            for item in details.get(key, []):
                results.append({
                    "type": key.upper(),
                    "identifier": item.get("identifier"),
                    "title": item.get("title"),
                    "note": item.get("applicability_note"),
                    "status": item.get("status"),
                    "source_url": item.get("source_url"),
                    "source_record_id": item.get("source_record_id"),
                })
        return results

    async def compliance_details_for_standard(self, standard_id: str) -> dict[str, list[dict[str, object]]]:
        standard = await self.get_by_id(standard_id)
        if standard is None:
            return {"bis_certification": [], "certification_schemes": [], "qco": [], "crs": [], "hallmarking": []}

        bis_certification: list[dict[str, object]] = []
        certification_schemes: list[dict[str, object]] = []
        qco_items: list[dict[str, object]] = []
        crs_items: list[dict[str, object]] = []
        hallmarking_items: list[dict[str, object]] = []

        if standard.source_record_id:
            cert_stmt = select(Certification).options(selectinload(Certification.source_record)).where(Certification.source_record_id == standard.source_record_id)
            for record in (await self.session.execute(cert_stmt)).scalars().all():
                source = record.source_record
                item = {
                    "identifier": record.external_identifier,
                    "title": record.title,
                    "scheme_name": record.scheme_name,
                    "applicability_note": record.applicability_note,
                    "status": "recorded",
                    "source_url": source.source_url if source else None,
                    "source_record_id": source.id if source else None,
                }
                certification_schemes.append(item)
                bis_certification.append({**item, "type": "BIS Certification"})

        qco_stmt = select(QcoMapping).options(selectinload(QcoMapping.qco_record).selectinload(QcoRecord.source_record)).where(QcoMapping.standard_id == standard_id)
        for mapping in (await self.session.execute(qco_stmt)).scalars().all():
            record = mapping.qco_record
            if record:
                source = getattr(record, "source_record", None)
                qco_items.append({
                    "identifier": record.notification_number,
                    "title": record.title,
                    "applicability_note": mapping.applicability_note,
                    "status": "recorded",
                    "source_url": source.source_url if source else None,
                    "source_record_id": source.id if source else None,
                })

        crs_stmt = select(CrsMapping).options(selectinload(CrsMapping.crs_record).selectinload(CrsRecord.source_record)).where(CrsMapping.standard_id == standard_id)
        for mapping in (await self.session.execute(crs_stmt)).scalars().all():
            record = mapping.crs_record
            if record:
                source = getattr(record, "source_record", None)
                crs_items.append({
                    "identifier": record.registration_number,
                    "title": record.title,
                    "applicability_note": mapping.applicability_note,
                    "status": "recorded",
                    "source_url": source.source_url if source else None,
                    "source_record_id": source.id if source else None,
                })

        if standard.source_record_id:
            hall_stmt = select(HallmarkingRule).options(selectinload(HallmarkingRule.source_record)).where(HallmarkingRule.source_record_id == standard.source_record_id)
            for record in (await self.session.execute(hall_stmt)).scalars().all():
                source = record.source_record
                hallmarking_items.append({
                    "identifier": record.rule_identifier,
                    "title": record.title,
                    "material": record.material,
                    "applicability_note": record.applicability_note,
                    "status": "recorded",
                    "source_url": source.source_url if source else None,
                    "source_record_id": source.id if source else None,
                })

        return {
            "bis_certification": bis_certification,
            "certification_schemes": certification_schemes,
            "qco": qco_items,
            "crs": crs_items,
            "hallmarking": hallmarking_items,
        }

    async def source_records_for_standard(self, standard_id: str) -> list[dict[str, object]]:
        standard = await self.get_by_id(standard_id)
        if standard is None:
            return []
        source_ids: set[str] = set()
        items: list[dict[str, object]] = []

        def add_source(source: SourceRecord | None, related: str) -> None:
            if source is None or source.id in source_ids:
                return
            source_ids.add(source.id)
            items.append({
                "source": source.source_type,
                "source_type": source.source_type,
                "source_url": source.source_url,
                "external_identifier": source.external_identifier,
                "retrieved_at": source.retrieved_at.isoformat() if source.retrieved_at else None,
                "related_standard": related,
                "source_status": source.source_status,
            })

        add_source(standard.source_record, standard.is_number)
        for version in standard.versions:
            add_source(version.source_record, standard.is_number)
            for amendment in version.amendments:
                add_source(amendment.source_record, standard.is_number)
        for relationship in (*standard.relationships_from, *standard.relationships_to):
            add_source(relationship.source_record, standard.is_number)
        return items

    async def evidence_bundle_for_standard(self, standard_id: str, text: str, terms: list[str], reasons: list[str]) -> list[dict[str, object]]:
        from app.application.requirement_mapping import build_requirement_mapping

        standard = await self.get_by_id(standard_id)
        if standard is None:
            return []

        items: list[dict[str, object]] = []
        source = standard.source_record
        items.append({
            "evidence_type": "Standard metadata",
            "evidence": f"{standard.is_number} — {standard.title}",
            "source": source.source_type if source else "database",
            "url": source.source_url if source else None,
            "timestamp": source.retrieved_at.isoformat() if source and source.retrieved_at else None,
            "related_standard": standard.is_number,
        })

        for version in standard.versions:
            version_source = version.source_record
            items.append({
                "evidence_type": "Version",
                "evidence": f"{version.edition_label} ({version.edition_year}) — {version.status}",
                "source": version_source.source_type if version_source else "database",
                "url": version_source.source_url if version_source else None,
                "timestamp": version_source.retrieved_at.isoformat() if version_source and version_source.retrieved_at else None,
                "related_standard": standard.is_number,
            })
            for amendment in version.amendments:
                amendment_source = amendment.source_record
                items.append({
                    "evidence_type": "Amendment",
                    "evidence": f"{amendment.amendment_label}: {amendment.title or 'Amendment recorded'}",
                    "source": amendment_source.source_type if amendment_source else "database",
                    "url": amendment_source.source_url if amendment_source else None,
                    "timestamp": amendment_source.retrieved_at.isoformat() if amendment_source and amendment_source.retrieved_at else None,
                    "related_standard": standard.is_number,
                })

        for relationship in (*standard.relationships_from, *standard.relationships_to):
            related = relationship.target_standard if relationship.source_standard_id == standard.id else relationship.source_standard
            rel_source = relationship.source_record
            items.append({
                "evidence_type": "Relationship",
                "evidence": f"{relationship.relationship_type}: {related.is_number} — {relationship.evidence_note or related.title}",
                "source": rel_source.source_type if rel_source else "database",
                "url": rel_source.source_url if rel_source else None,
                "timestamp": rel_source.retrieved_at.isoformat() if rel_source and rel_source.retrieved_at else None,
                "related_standard": standard.is_number,
            })

        compliance = await self.compliance_details_for_standard(standard_id)
        for category, records in compliance.items():
            for record in records:
                items.append({
                    "evidence_type": category.replace("_", " ").title(),
                    "evidence": record.get("title") or record.get("identifier"),
                    "source": "authoritative record",
                    "url": record.get("source_url"),
                    "timestamp": None,
                    "related_standard": standard.is_number,
                })

        for reason in reasons:
            items.append({
                "evidence_type": "Applicability signal",
                "evidence": reason,
                "source": "deterministic retrieval",
                "url": source.source_url if source else None,
                "timestamp": source.retrieved_at.isoformat() if source and source.retrieved_at else None,
                "related_standard": standard.is_number,
            })

        for row in build_requirement_mapping(text, terms, standard, reasons):
            items.append({
                "evidence_type": "Requirement mapping",
                "evidence": f"{row['requirement_element']}: {row['match']}",
                "source": row["supporting_evidence"],
                "url": source.source_url if source else None,
                "timestamp": None,
                "related_standard": standard.is_number,
            })

        return items


    async def get_many_by_ids(self, standard_ids: Sequence[str]) -> dict[str, Standard]:
        if not standard_ids:
            return {}
        statement = select(Standard).options(selectinload(Standard.source_record)).where(Standard.id.in_(standard_ids))
        rows = (await self.session.execute(statement)).scalars().all()
        return {standard.id: standard for standard in rows}

    async def add(self, standard: Standard) -> Standard:
        self.session.add(standard)
        await self.session.flush()
        return standard

    async def get_versions(self, standard_id: str) -> Sequence[StandardVersion]:
        result = await self.session.execute(select(StandardVersion).where(StandardVersion.standard_id == standard_id).order_by(StandardVersion.edition_year.desc().nullslast(), StandardVersion.edition_label))
        return result.scalars().all()

    async def get_relationships(self, standard_id: str) -> Sequence[StandardRelationship]:
        statement = (
            select(StandardRelationship)
            .options(selectinload(StandardRelationship.target_standard), selectinload(StandardRelationship.source_standard))
            .where((StandardRelationship.source_standard_id == standard_id) | (StandardRelationship.target_standard_id == standard_id))
            .order_by(StandardRelationship.relationship_type, StandardRelationship.created_at)
        )
        return (await self.session.execute(statement)).scalars().all()

    async def delete(self, standard: Standard) -> None:
        await self.session.delete(standard)
        await self.session.flush()