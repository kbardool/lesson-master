"""
Seed a lesson-master database from a versioned JSON snapshot.

Two schema versions are supported:

    v2.0  (default)  -> utils/seed_data_v2.0.json   current schema:
                        subjects / modules / module_topics / topic_exercises / ...
    v1.0             -> utils/seed_data_v1.0.json   original schema:
                        learning_plans / plan_items / exercises / ...

The loader is schema-agnostic: it inserts each table from the JSON snapshot in
the order the tables appear in the file, so it works for either version as long
as the target database already has that version's schema.

Typical use (fresh v2.0 database):

    alembic upgrade head
    python utils/seed_database.py                 # == --version 2.0

Seed a v1.0 (original) database instead:

    python utils/seed_database.py --version 1.0 --database ./python_learner.db

Flags:
    --version {1.0,2.0}   which schema version to seed (default: 2.0)
    --input PATH          JSON snapshot to load (default: seed_data_v<version>.json)
    --database URL/PATH   target DB (default: the app's configured database);
                          accepts a SQLAlchemy URL or a plain SQLite file path
    --force               seed even if the target database is not empty
"""

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Allow running as a script (`python utils/seed_database.py`) from the project
# root by putting the repo root (this file's parent's parent) on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SQLITE_URL, SessionLocal  # noqa: E402
from app.models import Module, Subject  # noqa: E402

UTILS_DIR = Path(__file__).resolve().parent

# Default snapshot per version.
SEED_FILES = {
    "1.0": UTILS_DIR / "seed_data_v1.0.json",
    "2.0": UTILS_DIR / "seed_data_v2.0.json",
}
DEFAULT_VERSION = "2.0"

# Backwards-compatible default (v2.0 snapshot) used by the tests.
SEED_FILE = SEED_FILES[DEFAULT_VERSION]


def load_seed_data(path: Path = SEED_FILE) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def is_empty(db: Session) -> bool:
    """True if a v2.0 database has no subjects and no modules yet."""
    return db.query(Subject).count() == 0 and db.query(Module).count() == 0


def _target_has_rows(db: Session, data: dict) -> bool:
    """Version-agnostic emptiness check: does the first snapshot table hold rows?"""
    first_table = next(iter(data), None)
    if first_table is None:
        return False
    count = db.execute(text(f"SELECT COUNT(*) FROM {first_table}")).scalar()
    return bool(count)


def seed(db: Session, data: dict) -> dict[str, int]:
    """Insert all rows from `data` into `db`, one table at a time, in file order.

    Works for any schema version because table and column names come straight
    from the JSON. Returns per-table insert counts.
    """
    counts: dict[str, int] = {}
    for table_name, rows in data.items():
        for row in rows:
            columns = ", ".join(row.keys())
            placeholders = ", ".join(f":{col}" for col in row)
            db.execute(
                text(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"),
                row,
            )
        counts[table_name] = len(rows)
    db.commit()
    return counts


def _make_session_factory(database: str | None) -> sessionmaker:
    """Return a session factory for the target database.

    Defaults to the app's configured database. A `--database` value may be a
    full SQLAlchemy URL (contains '://') or a plain SQLite file path.
    """
    if database is None:
        return SessionLocal
    url = database if "://" in database else f"sqlite:///{database}"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed a lesson-master database from a JSON snapshot.")
    parser.add_argument("--version", choices=sorted(SEED_FILES), default=DEFAULT_VERSION,
                        help="schema version to seed (default: %(default)s)")
    parser.add_argument("--input", type=Path, default=None,
                        help="JSON snapshot to load (default: seed_data_v<version>.json)")
    parser.add_argument("--database", default=None,
                        help="target database URL or SQLite path (default: the app's configured DB)")
    parser.add_argument("--force", action="store_true",
                        help="seed even if the target database already has data")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    seed_file = args.input or SEED_FILES[args.version]
    data = load_seed_data(seed_file)

    session_factory = _make_session_factory(args.database)
    db = session_factory()
    try:
        if _target_has_rows(db, data) and not args.force:
            print(
                "Target database already contains data. "
                "Refusing to seed a non-empty database (pass --force to override).",
                file=sys.stderr,
            )
            return 1
        print(f"Seeding v{args.version} from {seed_file} ...")
        counts = seed(db, data)
        for table_name, n in counts.items():
            print(f"  ✓ {table_name}: {n} rows")
        print("Done.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
