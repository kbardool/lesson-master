from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.topic import Topic


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
    title: Mapped[str]
    prompt: Mapped[str] = mapped_column(Text)
    starter_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_solution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(default="beginner")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    topic: Mapped[Topic] = relationship("Topic", back_populates="exercises")
    attempts: Mapped[list[ExerciseAttempt]] = relationship(
        "ExerciseAttempt",
        back_populates="exercise",
        cascade="all, delete-orphan",
        order_by="ExerciseAttempt.submitted_at",
    )

    # ---------- helpers ----------

    @property
    def latest_attempt(self) -> Optional[ExerciseAttempt]:
        return self.attempts[-1] if self.attempts else None

    @property
    def is_passed(self) -> bool:
        return any(a.status == "passed" for a in self.attempts)

    @property
    def status_label(self) -> str:
        if self.is_passed:
            return "passed"
        if self.attempts:
            return "attempted"
        return "not_started"

    def __repr__(self) -> str:
        return f"<Exercise id={self.id} title={self.title!r}>"


class ExerciseAttempt(Base):
    __tablename__ = "exercise_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"))
    code: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(default="attempted")  # attempted | passed | skipped
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    exercise: Mapped[Exercise] = relationship("Exercise", back_populates="attempts")

    def __repr__(self) -> str:
        return f"<ExerciseAttempt id={self.id} status={self.status!r}>"
