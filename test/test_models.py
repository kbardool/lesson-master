"""Unit tests for the renamed schema and the new Subject <-> Module relationship."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Exercise, Module, ModuleTopic, Subject, Topic


def test_renamed_table_names():
    assert Subject.__tablename__ == "subjects"
    assert Module.__tablename__ == "modules"
    assert ModuleTopic.__tablename__ == "module_topics"
    assert Exercise.__tablename__ == "topic_exercises"


def test_subject_module_many_to_many(db):
    subject = Subject(name="Python Advanced Programming")
    m1 = Module(name="Python Debugging")
    m2 = Module(name="Concurrency")
    subject.modules.extend([m1, m2])
    db.add(subject)
    db.commit()

    # subject -> modules
    db.refresh(subject)
    assert {m.name for m in subject.modules} == {"Python Debugging", "Concurrency"}

    # module -> subjects (both directions of the m2m)
    db.refresh(m1)
    assert [s.name for s in m1.subjects] == ["Python Advanced Programming"]

    # a module can belong to more than one subject
    other = Subject(name="Testing & QA")
    other.modules.append(m1)
    db.add(other)
    db.commit()
    db.refresh(m1)
    assert {s.name for s in m1.subjects} == {"Python Advanced Programming", "Testing & QA"}


def test_module_topic_unique_constraint(db):
    module = Module(name="M")
    topic = Topic(name="T", slug="t")
    db.add_all([module, topic])
    db.commit()

    db.add(ModuleTopic(module_id=module.id, topic_id=topic.id, position=0))
    db.commit()

    db.add(ModuleTopic(module_id=module.id, topic_id=topic.id, position=1))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_module_completion_helpers(db):
    module = Module(name="M")
    topics = [Topic(name=f"T{i}", slug=f"t{i}") for i in range(4)]
    db.add_all([module, *topics])
    db.commit()

    statuses = ["done", "done", "in_progress", "not_started"]
    for pos, (topic, status) in enumerate(zip(topics, statuses)):
        db.add(ModuleTopic(module_id=module.id, topic_id=topic.id, position=pos, status=status))
    db.commit()
    db.refresh(module)

    assert module.item_count == 4
    assert module.done_count == 2
    assert module.completion_pct == 50


def test_empty_module_completion_is_zero(db):
    module = Module(name="Empty")
    db.add(module)
    db.commit()
    db.refresh(module)
    assert module.completion_pct == 0
    assert module.item_count == 0
