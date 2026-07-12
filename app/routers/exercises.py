from typing import Optional

from app.templating import templates
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import exercise as ex_svc
from app.services import topic as topic_svc

router = APIRouter(prefix="/exercises", tags=["exercises"])


def _is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


@router.post("/", response_class=HTMLResponse)
def create_exercise(
    request: Request,
    topic_id: int = Form(...),
    title: str = Form(...),
    prompt: str = Form(...),
    starter_code: Optional[str] = Form(None),
    reference_solution: Optional[str] = Form(None),
    difficulty: str = Form("beginner"),
    db: Session = Depends(get_db),
):
    ex_svc.create_exercise(
        db,
        topic_id=topic_id,
        title=title,
        prompt=prompt,
        starter_code=starter_code or None,
        reference_solution=reference_solution or None,
        difficulty=difficulty,
    )
    topic = topic_svc.get_topic_by_id(db, topic_id)
    if _is_htmx(request) and topic:
        return templates.TemplateResponse(
            request, "partials/exercise_list.html",
            {"topic": topic},
        )
    if topic:
        return RedirectResponse(f"/topics/{topic.slug}", status_code=303)
    return RedirectResponse("/topics", status_code=303)


@router.get("/{exercise_id}", response_class=HTMLResponse)
def exercise_detail(exercise_id: int, request: Request, db: Session = Depends(get_db)):
    exercise = ex_svc.get_exercise(db, exercise_id)
    if not exercise:
        return HTMLResponse("<p>Exercise not found.</p>", status_code=404)
    return templates.TemplateResponse(
        request, "exercises/detail.html",
        {"exercise": exercise},
    )


@router.post("/{exercise_id}/attempts", response_class=HTMLResponse)
def submit_attempt(
    exercise_id: int,
    request: Request,
    code: str = Form(...),
    status: str = Form("attempted"),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    ex_svc.submit_attempt(db, exercise_id=exercise_id, code=code, status=status, notes=notes or None)
    exercise = ex_svc.get_exercise(db, exercise_id)
    if _is_htmx(request) and exercise:
        return templates.TemplateResponse(
            request, "partials/attempt_history.html",
            {"exercise": exercise},
        )
    return RedirectResponse(f"/exercises/{exercise_id}", status_code=303)


@router.delete("/{exercise_id}", response_class=HTMLResponse)
def delete_exercise(exercise_id: int, request: Request, db: Session = Depends(get_db)):
    ex_svc.delete_exercise(db, exercise_id)
    if _is_htmx(request):
        return HTMLResponse("")
    return RedirectResponse("/topics", status_code=303)
