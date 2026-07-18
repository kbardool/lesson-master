from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Table, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.topic import Topic


# Many-to-many link between subjects and modules:
#   a subject can have zero or more modules, and
#   a module can belong to zero or more subjects.
subject_modules = Table(
    "subject_modules",
    Base.metadata,
    Column("subject_id", ForeignKey("subjects.id"), primary_key=True),
    Column("module_id", ForeignKey("modules.id"), primary_key=True),
)


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    modules: Mapped[list[Module]] = relationship(
        "Module",
        secondary=subject_modules,
        back_populates="subjects",
        order_by="Module.name",
    )

    # ---------- helpers ----------

    @property
    def module_count(self) -> int:
        return len(self.modules)

    def __repr__(self) -> str:
        return f"<Subject id={self.id} name={self.name!r}>"


class Module(Base):
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(default="active")  # active | paused | completed
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    subjects: Mapped[list[Subject]] = relationship(
        "Subject",
        secondary=subject_modules,
        back_populates="modules",
        order_by="Subject.name",
    )

    module_topics: Mapped[list[ModuleTopic]] = relationship(
        "ModuleTopic",
        back_populates="module",
        order_by="ModuleTopic.position",
        cascade="all, delete-orphan",
    )

    # ---------- helpers ----------

    @property
    def completion_pct(self) -> int:
        if not self.module_topics:
            return 0
        done = sum(1 for mt in self.module_topics if mt.status == "done")
        return int(done / len(self.module_topics) * 100)

    @property
    def item_count(self) -> int:
        return len(self.module_topics)

    @property
    def done_count(self) -> int:
        return sum(1 for mt in self.module_topics if mt.status == "done")

    def __repr__(self) -> str:
        return f"<Module id={self.id} name={self.name!r}>"


class ModuleTopic(Base):
    __tablename__ = "module_topics"
    __table_args__ = (
        UniqueConstraint("module_id", "topic_id", name="uq_module_topic"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id"))
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
    position: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(default="not_started")  # not_started | in_progress | done
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    module: Mapped[Module] = relationship("Module", back_populates="module_topics")
    topic: Mapped[Topic] = relationship("Topic", back_populates="module_topics")

    def __repr__(self) -> str:
        return f"<ModuleTopic id={self.id} pos={self.position} status={self.status!r}>"
