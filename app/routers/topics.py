from typing import Optional

from app.templating import templates
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import topic as topic_svc
from app.services import exercise as ex_svc
from app.services import ai as ai_svc

router = APIRouter(prefix="/topics", tags=["topics"])


def _is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


@router.get("/", response_class=HTMLResponse)
def topics_index(request: Request, db: Session = Depends(get_db)):
    modules, orphan_topics = topic_svc.get_topics_grouped(db)
    all_topics = topic_svc.get_all_topics_flat(db)
    return templates.TemplateResponse(
        request, "topics/index.html",
        {"modules": modules, "orphan_topics": orphan_topics, "all_topics": all_topics},
    )


@router.post("/", response_class=HTMLResponse)
def create_topic(
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    difficulty: str = Form("beginner"),
    tags: Optional[str] = Form(None),
    parent_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    topic_svc.create_topic(
        db,
        name=name,
        description=description or None,
        difficulty=difficulty,
        tags=tags or None,
        parent_id=parent_id or None,
    )
    modules, orphan_topics = topic_svc.get_topics_grouped(db)
    all_topics = topic_svc.get_all_topics_flat(db)
    if _is_htmx(request):
        return templates.TemplateResponse(
            request, "partials/topic_list.html",
            {"modules": modules, "orphan_topics": orphan_topics, "all_topics": all_topics},
        )
    return RedirectResponse("/topics", status_code=303)


@router.get("/{slug}", response_class=HTMLResponse)
def topic_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    topic = topic_svc.get_topic_by_slug(db, slug)
    if not topic:
        return HTMLResponse("<p>Topic not found.</p>", status_code=404)
    all_topics = topic_svc.get_all_topics_flat(db)
    return templates.TemplateResponse(
        request, "topics/detail.html",
        {"topic": topic, "all_topics": all_topics},
    )


@router.delete("/{topic_id}", response_class=HTMLResponse)
def delete_topic(topic_id: int, request: Request, db: Session = Depends(get_db)):
    topic_svc.delete_topic(db, topic_id)
    if _is_htmx(request):
        return HTMLResponse("")
    return RedirectResponse("/topics", status_code=303)


@router.post("/{slug}/generate-exercises", response_class=HTMLResponse)
def generate_exercises(
    slug: str,
    request: Request,
    count: int = Form(3),
    db: Session = Depends(get_db),
):
    topic = topic_svc.get_topic_by_slug(db, slug)
    if not topic:
        return HTMLResponse("<p>Topic not found.</p>", status_code=404)

    try:
        generated = ai_svc.generate_exercises(
            topic_name=topic.name,
            description=topic.description,
            difficulty=topic.difficulty,
            count=count,
        )
    except EnvironmentError as e:
        return HTMLResponse(f'<p class="error-msg">⚠ {e}</p>', status_code=500)
    except ValueError as e:
        return HTMLResponse(f'<p class="error-msg">⚠ Failed to parse AI response: {e}</p>', status_code=500)

    for gen in generated:
        ex_svc.create_exercise(
            db,
            topic_id=topic.id,
            title=gen.title,
            prompt=gen.prompt,
            starter_code=gen.starter_code,
            reference_solution=gen.reference_solution,
            difficulty=gen.difficulty,
        )

    # Refresh topic from DB so exercises reflect the new additions
    db.refresh(topic)
    return templates.TemplateResponse(
        request, "partials/exercise_list.html",
        {"topic": topic},
    )
