import json
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Iterator
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
