from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.plan import LearningPlan, PlanItem


# ---------- queries ----------

def get_all_plans(db: Session) -> list[LearningPlan]:
    return db.query(LearningPlan).order_by(LearningPlan.created_at.desc()).all()


def get_plan(db: Session, plan_id: int) -> Optional[LearningPlan]:
    return db.get(LearningPlan, plan_id)


# ---------- mutations ----------

def create_plan(db: Session, *, name: str, description: Optional[str] = None) -> LearningPlan:
    plan = LearningPlan(name=name, description=description)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def update_plan_status(db: Session, plan_id: int, status: str) -> Optional[LearningPlan]:
    plan = db.get(LearningPlan, plan_id)
    if not plan:
        return None
    plan.status = status
    db.commit()
    db.refresh(plan)
    return plan


def delete_plan(db: Session, plan_id: int) -> bool:
    plan = db.get(LearningPlan, plan_id)
    if not plan:
        return False
    db.delete(plan)
    db.commit()
    return True


def add_topic_to_plan(db: Session, plan_id: int, topic_id: int) -> Optional[PlanItem]:
    """Appends a topic to a plan. Returns None if the topic is already in the plan."""
    next_pos = db.query(PlanItem).filter(PlanItem.plan_id == plan_id).count()
    item = PlanItem(plan_id=plan_id, topic_id=topic_id, position=next_pos)
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None  # UniqueConstraint violation — topic already in plan
    db.refresh(item)
    return item


def remove_item_from_plan(db: Session, item_id: int) -> bool:
    item = db.get(PlanItem, item_id)
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True


def update_item_status(db: Session, item_id: int, status: str) -> Optional[PlanItem]:
    item = db.get(PlanItem, item_id)
    if not item:
        return None
    item.status = status
    db.commit()
    db.refresh(item)
    return item


def update_item_notes(db: Session, item_id: int, notes: str) -> Optional[PlanItem]:
    item = db.get(PlanItem, item_id)
    if not item:
        return None
    item.notes = notes
    db.commit()
    db.refresh(item)
    return item


def reorder_items(db: Session, plan_id: int, ordered_item_ids: list[int]) -> None:
    """Rewrite positions based on a new order of item IDs."""
    items = {item.id: item for item in db.query(PlanItem).filter(PlanItem.plan_id == plan_id).all()}
    for position, item_id in enumerate(ordered_item_ids):
        if item_id in items:
            items[item_id].position = position
    db.commit()
