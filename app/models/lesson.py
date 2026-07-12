from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.topic import Topic


class TopicLesson(Base):
    __tablename__ = "topic_lessons"
    __table_args__ = (
        UniqueConstraint("topic_id", "level", name="uq_topic_lesson_level"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
    level: Mapped[str]  # basic | intermediate | advanced
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    topic: Mapped[Topic] = relationship("Topic", back_populates="lessons")

    def __repr__(self) -> str:
        return f"<TopicLesson topic_id={self.topic_id} level={self.level!r}>"
