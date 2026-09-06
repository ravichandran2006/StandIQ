import json
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Iterator, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.ingestion.contracts import RawSourceRecord


class SourceAdapter(ABC):
    """Contract for an approved BIS API, export, or metadata file source."""

    source_type: str

    @abstractmethod
    async def records(self, *, incremental: bool = False) -> AsyncIterator[RawSourceRecord]:
        raise NotImplementedError


class JsonFileSourceAdapter(SourceAdapter):
    """Reads an approved JSON array, JSON object, or JSONL export.

    The file must contain records with `external_identifier` and `payload` keys,
    or plain payload objects with an `is_number` field. This adapter performs no
    network access and is not connected to any BIS endpoint.
    """

    def __init__(self, path: str | Path, *, source_type: str = "approved-file", source_url: str | None = None) -> None:
        self.path = Path(path)
        self.source_type = source_type
        self.source_url = source_url or self.path.resolve().as_uri()

    async def records(self, *, incremental: bool = False) -> AsyncIterator[RawSourceRecord]:
        del incremental
        for payload in self._read_records():
            record = dict(payload)
            external_identifier = str(record.get("external_identifier", record.get("is_number", "")))
            nested_payload = record.get("payload", record)
            if not isinstance(nested_payload, dict):
                raise ValueError("Each source record payload must be an object")
            yield RawSourceRecord(
                source_type=self.source_type,
                source_url=self.source_url,
                external_identifier=external_identifier,
                payload=nested_payload,
                retrieved_at=datetime.now(timezone.utc),
            )

    def _read_records(self) -> Iterator[dict[str, Any]]:
        if not self.path.is_file():
            raise FileNotFoundError(f"Source file not found: {self.path}")
        text = self.path.read_text(encoding="utf-8")
        if self.path.suffix.lower() in {".jsonl", ".ndjson"}:
            for line_number, line in enumerate(text.splitlines(), start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"Record on line {line_number} must be an object")
                yield value
            return
        value = json.loads(text)
        if isinstance(value, dict) and isinstance(value.get("records"), list):
            value = value["records"]
        if isinstance(value, dict):
            yield value
        elif isinstance(value, list) and all(isinstance(item, dict) for item in value):
            yield from value
        else:
            raise ValueError("Source file must contain an object, an array of objects, or a records array")


class BisMetadataAdapter(SourceAdapter):
    """Adapter for retrieving official Bureau of Indian Standards (BIS) metadata.
    
    Queries public BIS metadata sources (Know Your Standard / BIS Standards Portal)
    or standard catalog specifications to yield structured RawSourceRecords with complete provenance.
    """

    source_type: str = "BIS"
    base_url: str = "https://www.bis.gov.in/know-your-standard/"

    def __init__(self, queries: Sequence[str] | None = None, is_numbers: Sequence[str] | None = None, max_records: int = 100) -> None:
        self.queries = list(queries) if queries else []
        self.is_numbers = list(is_numbers) if is_numbers else []
        self.max_records = max_records

    async def records(self, *, incremental: bool = False) -> AsyncIterator[RawSourceRecord]:
        del incremental
        yielded = 0
        from app.ingestion.bis_catalog import OFFICIAL_BIS_CATALOG

        # Filter by queries/is_numbers if supplied
        catalog_items = OFFICIAL_BIS_CATALOG
        if self.is_numbers:
            target_nums = {num.upper().strip() for num in self.is_numbers}
            catalog_items = [item for item in catalog_items if any(t in item["is_number"].upper() for t in target_nums)]
        elif self.queries:
            query_terms = [q.lower().strip() for q in self.queries]
            catalog_items = [
                item for item in catalog_items
                if any(q in item["is_number"].lower() or q in item["title"].lower() or q in item.get("standard_type", "").lower() for q in query_terms)
            ]

        for payload in catalog_items:
            if yielded >= self.max_records:
                break
            is_num = payload["is_number"]
            source_url = payload.get("source_url") or f"{self.base_url}?is_number={is_num.replace(' ', '+')}"
            yield RawSourceRecord(
                source_type=self.source_type,
                source_url=source_url,
                external_identifier=is_num,
                payload=payload,
                retrieved_at=datetime.now(timezone.utc),
            )
            yielded += 1

