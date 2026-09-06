import argparse
import asyncio
from pathlib import Path

from app.infrastructure.database import Database
from app.ingestion.adapters import JsonFileSourceAdapter
from app.ingestion.service import IngestionService
from app.settings import Settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest approved BIS metadata into StandIQ")
    parser.add_argument("--file", type=Path, default=None, help="Approved JSON, JSONL, or NDJSON metadata export")
    parser.add_argument("--query", type=str, default=None, help="Filter standards by keyword or query")
    parser.add_argument("--is-number", type=str, nargs="*", default=None, help="Filter by specific IS numbers")
    parser.add_argument("--source-type", default="BIS")
    parser.add_argument("--source-url", default=None)
    parser.add_argument("--mode", choices=("initial", "incremental", "full"), default="initial")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    return parser


async def run(args: argparse.Namespace) -> int:
    settings = Settings()
    database = Database(settings)
    if not database.configured:
        print("Database is not configured")
        return 1
    try:
        async for session in database.session():
            if args.file:
                adapter = JsonFileSourceAdapter(args.file, source_type=args.source_type, source_url=args.source_url)
            else:
                from app.ingestion.adapters import BisMetadataAdapter
                queries = [args.query] if args.query else None
                adapter = BisMetadataAdapter(queries=queries, is_numbers=args.is_number)
            
            stats = await IngestionService(session).ingest(adapter, mode="incremental" if args.mode == "incremental" else "full", dry_run=args.dry_run)
            print(stats.as_dict())
            return 0 if stats.failed == 0 else 2
    finally:
        await database.close()
    return 1


def main() -> int:
    return asyncio.run(run(build_parser().parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())

