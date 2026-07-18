from typing import Optional

from sqlalchemy.orm import Session

from app.models.module import Module, Subject


# ---------- queries ----------

def get_all_subjects(db: Session) -> list[Subject]:
    return db.query(Subject).order_by(Subject.name).all()


def get_subject(db: Session, subject_id: int) -> Optional[Subject]:
    return db.get(Subject, subject_id)


# ---------- mutations ----------

def create_subject(db: Session, *, name: str, description: Optional[str] = None) -> Subject:
    subject = Subject(name=name, description=description)
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


def delete_subject(db: Session, subject_id: int) -> bool:
    subject = db.get(Subject, subject_id)
    if not subject:
        return False
    db.delete(subject)
    db.commit()
    return True


def attach_module_to_subject(db: Session, subject_id: int, module_id: int) -> Optional[Subject]:
    """Link a module to a subject (idempotent). Returns None if either is missing."""
    subject = db.get(Subject, subject_id)
    module = db.get(Module, module_id)
    if not subject or not module:
        return None
    if module not in subject.modules:
        subject.modules.append(module)
        db.commit()
        db.refresh(subject)
    return subject


def detach_module_from_subject(db: Session, subject_id: int, module_id: int) -> Optional[Subject]:
    """Unlink a module from a subject. Returns None if the subject is missing."""
    subject = db.get(Subject, subject_id)
    if not subject:
        return None
    module = db.get(Module, module_id)
    if module and module in subject.modules:
        subject.modules.remove(module)
        db.commit()
        db.refresh(subject)
    return subject
