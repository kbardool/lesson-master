"""Unit tests for the module and subject service layers."""

from app.services import module as module_svc
from app.services import subject as subject_svc
from app.services import topic as topic_svc


def _make_topic(db, name):
    return topic_svc.create_topic(db, name=name)


def test_create_and_get_module(db):
    module = module_svc.create_module(db, name="Python Debugging", description="desc")
    assert module.id is not None
    assert module_svc.get_module(db, module.id).name == "Python Debugging"
    assert [m.id for m in module_svc.get_all_modules(db)] == [module.id]


def test_add_topic_to_module_and_dedupe(db):
    module = module_svc.create_module(db, name="M")
    topic = _make_topic(db, "Tracebacks")

    mt = module_svc.add_topic_to_module(db, module_id=module.id, topic_id=topic.id)
    assert mt is not None and mt.position == 0

    # adding the same topic again violates uq_module_topic -> None
    dup = module_svc.add_topic_to_module(db, module_id=module.id, topic_id=topic.id)
    assert dup is None


def test_update_status_and_reorder(db):
    module = module_svc.create_module(db, name="M")
    topics = [_make_topic(db, f"T{i}") for i in range(3)]
    mts = [module_svc.add_topic_to_module(db, module_id=module.id, topic_id=t.id) for t in topics]

    module_svc.update_module_topic_status(db, module_topic_id=mts[0].id, status="done")
    db.refresh(mts[0])
    assert mts[0].status == "done"

    # reverse the order
    module_svc.reorder_module_topics(db, module_id=module.id, ordered_ids=[mts[2].id, mts[1].id, mts[0].id])
    for mt in mts:
        db.refresh(mt)
    assert (mts[2].position, mts[1].position, mts[0].position) == (0, 1, 2)


def test_subject_create_attach_detach(db):
    subject = subject_svc.create_subject(db, name="Python Advanced Programming", description="d")
    module = module_svc.create_module(db, name="Python Debugging")

    subject_svc.attach_module_to_subject(db, subject_id=subject.id, module_id=module.id)
    db.refresh(subject)
    assert [m.name for m in subject.modules] == ["Python Debugging"]

    # attach is idempotent
    subject_svc.attach_module_to_subject(db, subject_id=subject.id, module_id=module.id)
    db.refresh(subject)
    assert len(subject.modules) == 1

    subject_svc.detach_module_from_subject(db, subject_id=subject.id, module_id=module.id)
    db.refresh(subject)
    assert subject.modules == []
