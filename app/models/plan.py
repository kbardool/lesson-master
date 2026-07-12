from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.topic import Topic


class LearningPlan(Base):
    __tablename__ = "learning_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(default="active")  # active | paused | completed
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    items: Mapped[list[PlanItem]] = relationship(
        "PlanItem",
        back_populates="plan",
        order_by="PlanItem.position",
        cascade="all, delete-orphan",
    )

    # ---------- helpers ----------

    @property
    def completion_pct(self) -> int:
        if not self.items:
            return 0
        done = sum(1 for i in self.items if i.status == "done")
        return int(done / len(self.items) * 100)

    @property
    def item_count(self) -> int:
        return len(self.items)

    @property
    def done_count(self) -> int:
        return sum(1 for i in self.items if i.status == "done")

    def __repr__(self) -> str:
        return f"<LearningPlan id={self.id} name={self.name!r}>"


class PlanItem(Base):
    __tablename__ = "plan_items"
    __table_args__ = (
        UniqueConstraint("plan_id", "topic_id", name="uq_plan_topic"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("learning_plans.id"))
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
    position: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(default="not_started")  # not_started | in_progress | done
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    plan: Mapped[LearningPlan] = relationship("LearningPlan", back_populates="items")
    topic: Mapped[Topic] = relationship("Topic", back_populates="plan_items")

    def __repr__(self) -> str:
        return f"<PlanItem id={self.id} pos={self.position} status={self.status!r}>"
