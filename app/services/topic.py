import re
from typing import Optional

from sqlalchemy.orm import Session

from app.models.topic import Topic


# ---------- internal ----------

def _slugify(name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", name.lower())
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug.strip("-")


def _unique_slug(db: Session, base_slug: str) -> str:
    slug = base_slug
    counter = 1
    while db.query(Topic).filter(Topic.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


# ---------- queries ----------

def get_all_root_topics(db: Session) -> list[Topic]:
    """Returns top-level topics (no parent), alphabetically."""
    return db.query(Topic).filter(Topic.parent_id.is_(None)).order_by(Topic.name).all()


def get_all_topics_flat(db: Session) -> list[Topic]:
    """All topics in a flat list — useful for <select> dropdowns."""
    return db.query(Topic).order_by(Topic.name).all()


def get_topics_grouped(db: Session):
    """
    Returns (modules, orphan_topics) where:
    - modules: all Modules ordered by creation date, each with .module_topics loaded
    - orphan_topics: root topics not belonging to any module, alphabetically
    """
    from app.models.module import Module

    modules = db.query(Module).order_by(Module.created_at).all()

    # Collect IDs of topics already assigned to at least one module
    assigned_ids: set[int] = {mt.topic_id for module in modules for mt in module.module_topics}

    orphan_query = db.query(Topic).filter(Topic.parent_id.is_(None))
    if assigned_ids:
        orphan_query = orphan_query.filter(Topic.id.notin_(assigned_ids))
    orphan_topics = orphan_query.order_by(Topic.name).all()

    return modules, orphan_topics


def get_topic_by_id(db: Session, topic_id: int) -> Optional[Topic]:
    return db.get(Topic, topic_id)


def get_topic_by_slug(db: Session, slug: str) -> Optional[Topic]:
    return db.query(Topic).filter(Topic.slug == slug).first()


# ---------- mutations ----------

def create_topic(
    db: Session,
    *,
    name: str,
    description: Optional[str] = None,
    difficulty: str = "beginner",
    tags: Optional[str] = None,
    parent_id: Optional[int] = None,
) -> Topic:
    slug = _unique_slug(db, _slugify(name))
    topic = Topic(
        name=name,
        slug=slug,
        description=description,
        difficulty=difficulty,
        tags=tags,
        parent_id=parent_id,
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


def update_topic(
    db: Session,
    topic_id: int,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    difficulty: Optional[str] = None,
    tags: Optional[str] = None,
) -> Optional[Topic]:
    topic = db.get(Topic, topic_id)
    if not topic:
        return None
    if name is not None:
        topic.name = name
    if description is not None:
        topic.description = description
    if difficulty is not None:
        topic.difficulty = difficulty
    if tags is not None:
        topic.tags = tags
    db.commit()
    db.refresh(topic)
    return topic


def delete_topic(db: Session, topic_id: int) -> bool:
    topic = db.get(Topic, topic_id)
    if not topic:
        return False
    db.delete(topic)
    db.commit()
    return True
