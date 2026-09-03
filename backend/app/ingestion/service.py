from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import IngestionRun
from app.ingestion.adapters import SourceAdapter
from app.ingestion.contracts import IngestionMode, IngestionStats, RawSourceRecord, StandardIngestionRecord
from app.ingestion.repository import IngestionRepository
from app.ingestion.transform import parse_standard, validate_standard


class IngestionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = IngestionRepository(session)

    async def ingest(self, adapter: SourceAdapter, *, mode: IngestionMode = "full", dry_run: bool = False) -> IngestionStats:
        stats = IngestionStats()
        if dry_run:
            async for raw in adapter.records(incremental=mode == "incremental"):
                stats.discovered += 1
                self._validate_only(raw, stats)
            return stats

        run = await self.repository.begin_run(adapter.source_type)
        try:
            async for raw in adapter.records(incremental=mode == "incremental"):
                stats.discovered += 1
                try:
                    async with self.session.begin_nested():
                        record = parse_standard(raw)
                        errors = validate_standard(record)
                        if errors:
                            stats.fail(f"{raw.external_identifier}: {'; '.join(errors)}")
                            continue
                        await self._ingest_record(record, run, stats)
                except Exception as exc:
                    stats.fail(f"{raw.external_identifier}: {type(exc).__name__}")
            await self.repository.finish_run(run, "failed" if stats.failed and not stats.inserted and not stats.updated else "completed", stats.as_dict())
            await self.session.commit()
        except Exception as exc:
            await self.session.rollback()
            stats.fail(f"adapter failure: {type(exc).__name__}")
            run = await self.repository.begin_run(adapter.source_type)
            await self.repository.finish_run(run, "failed", stats.as_dict())
            await self.session.commit()
        return stats

    def _validate_only(self, raw: RawSourceRecord, stats: IngestionStats) -> None:
        try:
            record = parse_standard(raw)
            errors = validate_standard(record)
            if errors:
                stats.fail(f"{raw.external_identifier}: {'; '.join(errors)}")
            else:
                stats.inserted += 1
        except Exception as exc:
            stats.fail(f"{raw.external_identifier}: {type(exc).__name__}")

    async def _ingest_record(self, record: StandardIngestionRecord, run: IngestionRun, stats: IngestionStats) -> None:
        source, source_created = await self.repository.upsert_source(record, run.id)
        standard, standard_created, standard_changed = await self.repository.upsert_standard(record, source)
        if standard_created:
            stats.inserted += 1
        elif standard_changed:
            stats.updated += 1
        else:
            stats.skipped += 1

        versions_by_label: dict[str, Any] = {}
        for item in record.versions:
            version, created = await self.repository.upsert_version(standard, item, source)
            versions_by_label[item.edition_label] = version
            if created and not standard_created:
                stats.updated += 1
            elif not created:
                stats.skipped += 1
            for amendment in record.amendments_by_edition.get(item.edition_label, ()):
                if await self.repository.upsert_amendment(version, amendment, source):
                    stats.updated += 1
                else:
                    stats.skipped += 1

        for item in record.classifications:
            await self.repository.upsert_classification(standard, item)
        for item in record.relationships:
            created, target_found = await self.repository.upsert_relationship(standard, item, source)
            if not target_found:
                stats.fail(f"{record.is_number}: relationship target not found: {item.target_is_number}")
            elif created:
                stats.updated += 1
            else:
                stats.skipped += 1
        for item in record.certifications:
            await self.repository.upsert_certification(item, source)
        for item in record.qco_records:
            await self.repository.upsert_regulatory(standard, item, source, "qco")
        for item in record.crs_records:
            await self.repository.upsert_regulatory(standard, item, source, "crs")
        for item in record.hallmarking_rules:
            await self.repository.upsert_regulatory(standard, item, source, "hallmarking")
