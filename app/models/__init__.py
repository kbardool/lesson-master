# Importing all models here ensures SQLAlchemy registers them
# with Base.metadata before create_all() or Alembic autogenerate runs.
from app.models.topic import Topic
from app.models.exercise import Exercise, ExerciseAttempt
from app.models.module import Subject, Module, ModuleTopic, subject_modules
from app.models.lesson import TopicLesson

__all__ = [
    "Topic",
    "Exercise",
    "ExerciseAttempt",
    "Subject",
    "Module",
    "ModuleTopic",
    "subject_modules",
    "TopicLesson",
]
