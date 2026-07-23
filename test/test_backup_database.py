"""Tests for utils/backup_database.py: raw dump correctness and round-tripping
through utils/seed_database.py."""

import json

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.services import module as module_svc
from app.services import subject as subject_svc
from app.services import topic as topic_svc
from utils import backup_database, seed_database


def _seed_sample_data(db):
    subject = subject_svc.create_subject(
        db, name="Python Advanced Programming", description="Advanced Python topics."
    )
    module = module_svc.create_module(db, name="Python Debugging", description="Debugging techniques.")
    subject_svc.attach_module_to_subject(db, subject_id=subject.id, module_id=module.id)
    topic = topic_svc.create_topic(db, name="pdb basics", description="Intro to pdb.")
    module_topic = module_svc.add_topic_to_module(db, module_id=module.id, topic_id=topic.id)
    return subject, module, topic, module_topic


def test_dump_preserves_ids_and_relations(db, engine):
    subject, module, topic, module_topic = _seed_sample_data(db)

    data = backup_database.dump(engine)

    assert data["subjects"][0]["id"] == subject.id
    assert data["subjects"][0]["name"] == "Python Advanced Programming"
    assert data["modules"][0]["id"] == module.id
    assert data["subject_modules"] == [{"subject_id": subject.id, "module_id": module.id}]
    assert data["topics"][0]["id"] == topic.id
    assert data["module_topics"][0] == {
        "id": module_topic.id,
        "module_id": module.id,
        "topic_id": topic.id,
        "position": module_topic.position,
        "status": module_topic.status,
        "notes": module_topic.notes,
    }
    # Tables with no rows are simply absent/empty, not errors.
    assert data.get("exercise_attempts", []) == []


def test_dump_preserves_timestamp_strings_verbatim(db, engine):
    subject_svc.create_subject(db, name="S")
    with engine.connect() as conn:
        raw_created_at = conn.execute(text("SELECT created_at FROM subjects")).scalar()

    data = backup_database.dump(engine)
    assert data["subjects"][0]["created_at"] == raw_created_at


def test_backup_writes_json_file(db, engine, tmp_path):
    _seed_sample_data(db)
    output = tmp_path / "out.json"

    result_path, counts = backup_database.backup(database=str(engine.url), output=output)

    assert result_path == output
    assert output.exists()
    assert counts["subjects"] == 1
    assert counts["modules"] == 1
    assert counts["topics"] == 1

    data = json.loads(output.read_text())
    assert data["subjects"][0]["name"] == "Python Advanced Programming"


def test_backup_default_output_path_and_naming(db, engine, tmp_path, monkeypatch):
    _seed_sample_data(db)
    monkeypatch.setattr(backup_database, "BACKUPS_DIR", tmp_path / "backups")

    result_path, _ = backup_database.backup(database=str(engine.url))

    assert result_path.parent == tmp_path / "backups"
    assert result_path.name.startswith("backup_")
    assert result_path.suffix == ".json"


def test_backup_round_trips_through_seed_database(db, engine, tmp_path):
    _seed_sample_data(db)
    output = tmp_path / "out.json"
    backup_database.backup(database=str(engine.url), output=output)

    dest_db_path = tmp_path / "dest.db"
    dest_engine = create_engine(f"sqlite:///{dest_db_path}")
    Base.metadata.create_all(dest_engine)
    DestSession = sessionmaker(bind=dest_engine, autoflush=False, autocommit=False)
    dest_session = DestSession()
    try:
        data = seed_database.load_seed_data(output)
        counts = seed_database.seed(dest_session, data)
        assert counts["subjects"] == 1
        assert counts["modules"] == 1
        assert counts["topics"] == 1
        assert counts["module_topics"] == 1
        assert counts["subject_modules"] == 1

        tables = ["subjects", "modules", "subject_modules", "topics", "module_topics"]
        with engine.connect() as src_conn, dest_engine.connect() as dst_conn:
            for table in tables:
                src_rows = [dict(r) for r in src_conn.execute(text(f"SELECT * FROM {table} ORDER BY rowid")).mappings()]
                dst_rows = [dict(r) for r in dst_conn.execute(text(f"SELECT * FROM {table} ORDER BY rowid")).mappings()]
                assert src_rows == dst_rows, f"mismatch in table {table}"
    finally:
        dest_session.close()
        dest_engine.dispose()
