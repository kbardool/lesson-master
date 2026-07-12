from typing import Optional

from sqlalchemy.orm import Session

from app.models.exercise import Exercise, ExerciseAttempt


def get_exercise(db: Session, exercise_id: int) -> Optional[Exercise]:
    return db.get(Exercise, exercise_id)


def create_exercise(
    db: Session,
    *,
    topic_id: int,
    title: str,
    prompt: str,
    starter_code: Optional[str] = None,
    reference_solution: Optional[str] = None,
    difficulty: str = "beginner",
) -> Exercise:
    exercise = Exercise(
        topic_id=topic_id,
        title=title,
        prompt=prompt,
        starter_code=starter_code,
        reference_solution=reference_solution,
        difficulty=difficulty,
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise


def delete_exercise(db: Session, exercise_id: int) -> bool:
    exercise = db.get(Exercise, exercise_id)
    if not exercise:
        return False
    db.delete(exercise)
    db.commit()
    return True


def submit_attempt(
    db: Session,
    *,
    exercise_id: int,
    code: str,
    status: str = "attempted",
    notes: Optional[str] = None,
) -> ExerciseAttempt:
    attempt = ExerciseAttempt(
        exercise_id=exercise_id,
        code=code,
        status=status,
        notes=notes,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt
