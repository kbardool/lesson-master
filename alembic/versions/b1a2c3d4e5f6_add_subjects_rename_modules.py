"""add subjects, rename plans->modules and related tables

Renames the plan-centric schema to the subject/module-centric schema:

    learning_plans   -> modules
    plan_items       -> module_topics   (column plan_id -> module_id)
    exercises        -> topic_exercises

and introduces two new tables:

    subjects            (the new top of the hierarchy)
    subject_modules     (many-to-many: subjects <-> modules)

This migration is schema-only; content (including the seeded
"Python Advanced Programming" subject) is loaded via utils/seed_database.py.

`plan_items` is rebuilt as `module_topics` explicitly (create + copy + drop)
rather than via batch_alter_table, because SQLite unique-constraint reflection
inside a batch recreate is unreliable and would silently drop the constraint.

Revision ID: b1a2c3d4e5f6
Revises: 623ae4287a2d
Create Date: 2026-07-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1a2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "623ae4287a2d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # --- straightforward table renames (SQLite auto-updates FK references) ---
    op.rename_table("learning_plans", "modules")
    op.rename_table("exercises", "topic_exercises")

    # --- rebuild plan_items as module_topics (plan_id -> module_id) ---
    op.create_table(
        "module_topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"]),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("module_id", "topic_id", name="uq_module_topic"),
    )
    op.execute(
        "INSERT INTO module_topics (id, module_id, topic_id, position, status, notes) "
        "SELECT id, plan_id, topic_id, position, status, notes FROM plan_items"
    )
    op.drop_table("plan_items")

    # --- new tables ---
    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "subject_modules",
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"]),
        sa.PrimaryKeyConstraint("subject_id", "module_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("subject_modules")
    op.drop_table("subjects")

    # --- rebuild module_topics back into plan_items (module_id -> plan_id) ---
    op.create_table(
        "plan_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["plan_id"], ["modules.id"]),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plan_id", "topic_id", name="uq_plan_topic"),
    )
    op.execute(
        "INSERT INTO plan_items (id, plan_id, topic_id, position, status, notes) "
        "SELECT id, module_id, topic_id, position, status, notes FROM module_topics"
    )
    op.drop_table("module_topics")

    # --- rename tables back (SQLite retargets plan_items.plan_id FK to learning_plans) ---
    op.rename_table("topic_exercises", "exercises")
    op.rename_table("modules", "learning_plans")
