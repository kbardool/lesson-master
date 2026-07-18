"""Test that the JSON seed loader populates an empty database correctly,
including the new subject and its link to the existing module."""

from app.models import Module, Subject
from utils import seed_database


def test_seed_populates_empty_database(db):
    assert seed_database.is_empty(db)

    data = seed_database.load_seed_data()
    counts = seed_database.seed(db, data)

    # every table listed in the snapshot is inserted
    assert counts["topics"] == 16
    assert counts["modules"] == 1
    assert counts["module_topics"] == 16
    assert counts["topic_exercises"] == 5
    assert counts["topic_lessons"] == 4
    assert counts["subjects"] == 1
    assert counts["subject_modules"] == 1

    assert not seed_database.is_empty(db)


def test_seed_links_subject_to_python_debugging(db):
    seed_database.seed(db, seed_database.load_seed_data())

    subject = db.query(Subject).filter(Subject.name == "Python Advanced Programming").one()
    assert subject.description and "high-performance applications" in subject.description
    assert [m.name for m in subject.modules] == ["Python Debugging"]

    # and the module knows about the subject (reverse side of the m2m)
    module = db.query(Module).filter(Module.name == "Python Debugging").one()
    assert "Python Advanced Programming" in [s.name for s in module.subjects]
