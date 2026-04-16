"""
ETL script: Export inference logs from MongoDB, transform, load into PostgreSQL for analytics.

Usage:
    python scripts/etl_inference_logs.py [--since-hours 24] [--dry-run]

Why this exists:
    - MongoDB stores raw inference logs (high-write, schema-flexible)
    - PostgreSQL stores structured analytics data (query-efficient, index-optimized)
    - This ETL bridges the two, demonstrating data pipeline skills
"""
import argparse
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from datetime import datetime, timedelta

from sqlalchemy import text
from app.db.postgres import async_session, engine
from app.db.mongo import mongo_db


async def extract(since_hours: int) -> list[dict]:
    collection = mongo_db.inference_logs
    cutoff = datetime.utcnow() - timedelta(hours=since_hours)
    cursor = collection.find({"_id": {"$gte": cutoff}})
    logs = await cursor.to_list(length=None)
    print(f"  Extracted {len(logs)} logs from MongoDB (last {since_hours}h)")
    return logs


async def transform(logs: list[dict]) -> list[dict]:
    records = []
    for log in logs:
        records.append({
            "task_id": log.get("task_id", ""),
            "latency": log.get("latency", 0),
            "status": log.get("status", "unknown"),
            "chunk_count": log.get("chunk_count", 0),
            "logged_at": log.get("_id").generation_time.isoformat() if hasattr(log.get("_id"), "generation_time") else datetime.utcnow().isoformat(),
        })
    print(f"  Transformed {len(records)} records")
    return records


async def load(records: list[dict], dry_run: bool = False):
    if dry_run:
        print(f"  [DRY RUN] Would load {len(records)} records into PostgreSQL")
        for r in records[:3]:
            print(f"    {r}")
        return

    async with async_session() as session:
        for r in records:
            await session.execute(
                text("""
                    INSERT INTO inference_analytics (task_id, latency, status, chunk_count, logged_at)
                    VALUES (:task_id, :latency, :status, :chunk_count, :logged_at)
                    ON CONFLICT (task_id) DO UPDATE SET
                        latency = EXCLUDED.latency,
                        status = EXCLUDED.status
                """),
                r,
            )
        await session.commit()
    print(f"  Loaded {len(records)} records into PostgreSQL")


async def ensure_table():
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS inference_analytics (
                task_id VARCHAR(36) PRIMARY KEY,
                latency FLOAT DEFAULT 0,
                status VARCHAR(20) DEFAULT 'unknown',
                chunk_count INTEGER DEFAULT 0,
                logged_at TIMESTAMP DEFAULT NOW()
            )
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_analytics_status
            ON inference_analytics (status)
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_analytics_logged_at
            ON inference_analytics (logged_at)
        """))
    print("  Ensured inference_analytics table exists")


async def run(since_hours: int, dry_run: bool):
    print("ETL Pipeline: MongoDB → PostgreSQL")
    print("=" * 40)

    print("[1/3] Extract...")
    logs = await extract(since_hours)

    print("[2/3] Transform...")
    records = await transform(logs)

    print("[3/3] Load...")
    if not dry_run:
        await ensure_table()
    await load(records, dry_run)

    print("=" * 40)
    print("ETL complete.")


def main():
    parser = argparse.ArgumentParser(description="ETL: MongoDB inference logs → PostgreSQL analytics")
    parser.add_argument("--since-hours", type=int, default=24, help="Extract logs from last N hours")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing to PostgreSQL")
    args = parser.parse_args()
    asyncio.run(run(args.since_hours, args.dry_run))


if __name__ == "__main__":
    main()
