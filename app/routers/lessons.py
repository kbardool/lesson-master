from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import ai as ai_svc
from app.services import lesson as lesson_svc
from app.services import topic as topic_svc
from app.templating import templates

router = APIRouter(prefix="/topics", tags=["lessons"])


def _is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


def _lesson_panel_response(request, topic, level, error=None):
    """Helper: return the lesson panel partial for a given level."""
    lesson = topic.lessons_by_level.get(level)
    return templates.TemplateResponse(
        request, "partials/lesson_panel.html",
        {"topic": topic, "level": level, "lesson": lesson, "lesson_error": error},
    )


@router.post("/{slug}/generate-lesson", response_class=HTMLResponse)
def generate_lesson(
    slug: str,
    request: Request,
    level: str = Form("basic"),
    db: Session = Depends(get_db),
):
    topic = topic_svc.get_topic_by_slug(db, slug)
    if not topic:
        return HTMLResponse("<p>Topic not found.</p>", status_code=404)

    try:
        content = ai_svc.generate_lesson(
            topic_name=topic.name,
            description=topic.description,
            difficulty=topic.difficulty,
            level=level,
        )
    except Exception as e:
        db.refresh(topic)
        return _lesson_panel_response(request, topic, level, error=str(e))

    lesson_svc.upsert_lesson(db, topic_id=topic.id, level=level, content=content)
    db.refresh(topic)
    return _lesson_panel_response(request, topic, level)


@router.post("/{slug}/lesson/{level}/save", response_class=HTMLResponse)
def save_lesson(
    slug: str,
    level: str,
    request: Request,
    content: str = Form(...),
    db: Session = Depends(get_db),
):
    topic = topic_svc.get_topic_by_slug(db, slug)
    if not topic:
        return HTMLResponse("<p>Topic not found.</p>", status_code=404)

    lesson_svc.upsert_lesson(db, topic_id=topic.id, level=level, content=content)
    db.refresh(topic)
    return _lesson_panel_response(request, topic, level)


@router.delete("/{slug}/lesson/{level}", response_class=HTMLResponse)
def delete_lesson(
    slug: str,
    level: str,
    request: Request,
    db: Session = Depends(get_db),
):
    topic = topic_svc.get_topic_by_slug(db, slug)
    if not topic:
        return HTMLResponse("<p>Topic not found.</p>", status_code=404)

    lesson_svc.delete_lesson(db, topic_id=topic.id, level=level)
    db.refresh(topic)
    return _lesson_panel_response(request, topic, level)
