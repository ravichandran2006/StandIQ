import argparse
import asyncio
import time
from typing import Any

from sqlalchemy import func, select

from app.domain.models import Amendment, SourceRecord, Standard, StandardRelationship
from app.infrastructure.database import Database
from app.ingestion.adapters import BisMetadataAdapter
from app.ingestion.service import IngestionService
from app.settings import get_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest official BIS Indian Standards metadata into StandIQ")
    parser.add_argument("--mode", choices=("initial", "incremental", "full"), default="initial", help="Ingestion run mode")
    parser.add_argument("--query", type=str, default=None, help="Filter standards by keyword or search query")
    parser.add_argument("--is-number", type=str, nargs="*", default=None, help="Filter by specific IS numbers")
    parser.add_argument("--resume", action="store_true", help="Resume previous ingestion run")
    parser.add_argument("--dry-run", action="store_true", help="Validate without committing to database")
    parser.add_argument("--max-records", type=int, default=100, help="Maximum number of standards to ingest")
    return parser


async def run(args: argparse.Namespace) -> int:
    start_time = time.monotonic()
    settings = get_settings()
    database = Database(settings)
    if not database.configured:
        print("Error: Database is not configured in .env (DATABASE_URL)")
        return 1

    try:
        async for session in database.session():
            queries = [args.query] if args.query else None
            adapter = BisMetadataAdapter(queries=queries, is_numbers=args.is_number, max_records=args.max_records)
            
            service = IngestionService(session)
            ingest_mode = "incremental" if args.mode == "incremental" else "full"
            stats = await service.ingest(adapter, mode=ingest_mode, dry_run=args.dry_run)
            
            # Fetch relational summary metrics
            standards_count = int((await session.execute(select(func.count()).select_from(Standard))).scalar_one())
            relationships_count = int((await session.execute(select(func.count()).select_from(StandardRelationship))).scalar_one())
            amendments_count = int((await session.execute(select(func.count()).select_from(Amendment))).scalar_one())
            provenance_count = int((await session.execute(select(func.count()).select_from(SourceRecord))).scalar_one())
            
            elapsed = round(time.monotonic() - start_time, 2)
            
            result_output: dict[str, Any] = {
                "status": "completed" if stats.failed == 0 else "completed_with_errors",
                "discovered": stats.discovered,
                "parsed": stats.discovered,
                "valid": stats.discovered - stats.failed,
                "inserted": stats.inserted,
                "updated": stats.updated,
                "skipped": stats.skipped,
                "duplicates": stats.skipped,
                "failed": stats.failed,
                "relationships": relationships_count,
                "amendments": amendments_count,
                "provenance": provenance_count,
                "postgresql_standards_count": standards_count,
                "elapsed_time": f"{elapsed}s",
                "errors": stats.errors,
            }
            
            print("\n" + "=" * 50)
            print("STANDIQ BIS INGESTION SUMMARY")
            print("=" * 50)
            for key, val in result_output.items():
                print(f"  {key:<27}: {val}")
            print("=" * 50 + "\n")
            
            return 0 if stats.failed == 0 else 2
    finally:
        await database.close()
    return 1


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
