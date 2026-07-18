from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.module import Module, ModuleTopic


# ---------- queries ----------

def get_all_modules(db: Session) -> list[Module]:
    return db.query(Module).order_by(Module.created_at.desc()).all()


def get_module(db: Session, module_id: int) -> Optional[Module]:
    return db.get(Module, module_id)


# ---------- mutations ----------

def create_module(db: Session, *, name: str, description: Optional[str] = None) -> Module:
    module = Module(name=name, description=description)
    db.add(module)
    db.commit()
    db.refresh(module)
    return module


def update_module_status(db: Session, module_id: int, status: str) -> Optional[Module]:
    module = db.get(Module, module_id)
    if not module:
        return None
    module.status = status
    db.commit()
    db.refresh(module)
    return module


def delete_module(db: Session, module_id: int) -> bool:
    module = db.get(Module, module_id)
    if not module:
        return False
    db.delete(module)
    db.commit()
    return True


def add_topic_to_module(db: Session, module_id: int, topic_id: int) -> Optional[ModuleTopic]:
    """Appends a topic to a module. Returns None if the topic is already in the module."""
    next_pos = db.query(ModuleTopic).filter(ModuleTopic.module_id == module_id).count()
    module_topic = ModuleTopic(module_id=module_id, topic_id=topic_id, position=next_pos)
    db.add(module_topic)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None  # UniqueConstraint violation — topic already in module
    db.refresh(module_topic)
    return module_topic


def remove_topic_from_module(db: Session, module_topic_id: int) -> bool:
    module_topic = db.get(ModuleTopic, module_topic_id)
    if not module_topic:
        return False
    db.delete(module_topic)
    db.commit()
    return True


def update_module_topic_status(db: Session, module_topic_id: int, status: str) -> Optional[ModuleTopic]:
    module_topic = db.get(ModuleTopic, module_topic_id)
    if not module_topic:
        return None
    module_topic.status = status
    db.commit()
    db.refresh(module_topic)
    return module_topic


def update_module_topic_notes(db: Session, module_topic_id: int, notes: str) -> Optional[ModuleTopic]:
    module_topic = db.get(ModuleTopic, module_topic_id)
    if not module_topic:
        return None
    module_topic.notes = notes
    db.commit()
    db.refresh(module_topic)
    return module_topic


def reorder_module_topics(db: Session, module_id: int, ordered_ids: list[int]) -> None:
    """Rewrite positions based on a new order of module_topic IDs."""
    rows = {
        mt.id: mt
        for mt in db.query(ModuleTopic).filter(ModuleTopic.module_id == module_id).all()
    }
    for position, module_topic_id in enumerate(ordered_ids):
        if module_topic_id in rows:
            rows[module_topic_id].position = position
    db.commit()
