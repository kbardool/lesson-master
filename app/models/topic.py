from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.exercise import Exercise
    from app.models.module import ModuleTopic
    from app.models.lesson import TopicLesson


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True)
    slug: Mapped[str] = mapped_column(unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(default="beginner")  # beginner | intermediate | advanced
    tags: Mapped[Optional[str]] = mapped_column(nullable=True)   # comma-separated
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("topics.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Self-referential hierarchy
    parent: Mapped[Optional[Topic]] = relationship(
        "Topic", remote_side="Topic.id", back_populates="children"
    )
    children: Mapped[list[Topic]] = relationship(
        "Topic", back_populates="parent", order_by="Topic.name"
    )

    # Cross-model relationships (strings avoid circular imports)
    exercises: Mapped[list[Exercise]] = relationship(
        "Exercise", back_populates="topic", cascade="all, delete-orphan", order_by="Exercise.id"
    )
    module_topics: Mapped[list[ModuleTopic]] = relationship("ModuleTopic", back_populates="topic")
    lessons: Mapped[list[TopicLesson]] = relationship(
        "TopicLesson", back_populates="topic", cascade="all, delete-orphan"
    )

    # ---------- helpers ----------

    @property
    def tag_list(self) -> list[str]:
        return [t.strip() for t in self.tags.split(",")] if self.tags else []

    @property
    def exercise_count(self) -> int:
        return len(self.exercises)

    @property
    def passed_exercise_count(self) -> int:
        return sum(1 for e in self.exercises if e.is_passed)

    @property
    def lessons_by_level(self) -> dict[str, TopicLesson]:
        return {lesson.level: lesson for lesson in self.lessons}

    def __repr__(self) -> str:
        return f"<Topic id={self.id} slug={self.slug!r}>"
