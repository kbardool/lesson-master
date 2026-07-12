from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.lesson import TopicLesson

LEVELS = ("basic", "intermediate", "advanced")


def get_lesson(db: Session, topic_id: int, level: str) -> Optional[TopicLesson]:
    return (
        db.query(TopicLesson)
        .filter(TopicLesson.topic_id == topic_id, TopicLesson.level == level)
        .first()
    )


def upsert_lesson(db: Session, *, topic_id: int, level: str, content: str) -> TopicLesson:
    """Create or overwrite the lesson for a given topic + level."""
    lesson = get_lesson(db, topic_id, level)
    if lesson:
        lesson.content = content
        lesson.updated_at = datetime.now()
    else:
        lesson = TopicLesson(topic_id=topic_id, level=level, content=content)
        db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


def delete_lesson(db: Session, topic_id: int, level: str) -> bool:
    lesson = get_lesson(db, topic_id, level)
    if not lesson:
        return False
    db.delete(lesson)
    db.commit()
    return True
