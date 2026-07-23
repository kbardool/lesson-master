"""
Back up the lesson-master database to a portable JSON snapshot.

Writes every row of every table, in FK-safe (parent-before-child) order, to
backups/backup_<YYYYMMDD>_<HHMMSS>.json. Primary keys, foreign keys, and
timestamp columns are copied verbatim (no reformatting), so the resulting
file has the same shape as utils/seed_data_v2.0.json and can be reloaded with:

    python utils/seed_database.py --input backups/backup_<...>.json

Usage:
    python utils/backup_database.py
    python utils/backup_database.py --database ./data/lesson_master.db
    python utils/backup_database.py --output backups/pre-migration.json
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, text

# Allow running as a script (`python utils/backup_database.py`) from the
# project root by putting the repo root on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SQLITE_URL  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKUPS_DIR = PROJECT_ROOT / "backups"

# Tables in FK-safe order: every table only references tables earlier in this
# list (subjects/modules before their join table, topics before module_topics,
# topics before topic_exercises/topic_lessons, topic_exercises before
# exercise_attempts). Mirrors the layout of utils/seed_data_v2.0.json.
TABLES = [
    "subjects",
    "modules",
    "subject_modules",
    "topics",
    "module_topics",
    "topic_exercises",
    "exercise_attempts",
    "topic_lessons",
]

# Composite-key tables have no `id` column to order by.
ORDER_BY = {
    "subject_modules": "subject_id, module_id",
}


def _resolve_url(database: str | None) -> str:
    """A `--database` value may be a full SQLAlchemy URL or a plain SQLite path."""
    if database is None:
        return SQLITE_URL
    return database if "://" in database else f"sqlite:///{database}"


def dump(engine) -> dict[str, list[dict]]:
    """Read every row of every known table, preserving values exactly as stored."""
    data: dict[str, list[dict]] = {}
    with engine.connect() as conn:
        existing = {
            row[0]
            for row in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        }
        for table in TABLES:
            if table not in existing:
                continue
            order_by = ORDER_BY.get(table, "id")
            rows = conn.execute(text(f"SELECT * FROM {table} ORDER BY {order_by}")).mappings().all()
            data[table] = [dict(row) for row in rows]
    return data


def backup(database: str | None = None, output: Path | None = None) -> tuple[Path, dict[str, int]]:
    engine = create_engine(_resolve_url(database), connect_args={"check_same_thread": False})
    try:
        data = dump(engine)
    finally:
        engine.dispose()

    if output is None:
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = BACKUPS_DIR / f"backup_{timestamp}.json"
    else:
        output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return output, {table: len(rows) for table, rows in data.items()}


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Back up the lesson-master database to a JSON snapshot.")
    parser.add_argument("--database", default=None,
                        help="source database URL or SQLite path (default: the app's configured DB)")
    parser.add_argument("--output", type=Path, default=None,
                        help="output JSON path (default: backups/backup_<timestamp>.json)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    output, counts = backup(database=args.database, output=args.output)
    print(f"Backed up to {output}")
    for table, n in counts.items():
        print(f"  ✓ {table}: {n} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
