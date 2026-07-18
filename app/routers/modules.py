from typing import Optional

from app.templating import templates
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import module as module_svc
from app.services import topic as topic_svc

router = APIRouter(prefix="/modules", tags=["modules"])


def _is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


@router.get("/", response_class=HTMLResponse)
def modules_index(request: Request, db: Session = Depends(get_db)):
    modules = module_svc.get_all_modules(db)
    return templates.TemplateResponse(
        request, "modules/index.html",
        {"modules": modules},
    )


@router.post("/", response_class=HTMLResponse)
def create_module(
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    module_svc.create_module(db, name=name, description=description or None)
    modules = module_svc.get_all_modules(db)
    if _is_htmx(request):
        return templates.TemplateResponse(
            request, "partials/module_list.html",
            {"modules": modules},
        )
    return RedirectResponse("/modules", status_code=303)


@router.get("/{module_id}", response_class=HTMLResponse)
def module_detail(module_id: int, request: Request, db: Session = Depends(get_db)):
    module = module_svc.get_module(db, module_id)
    if not module:
        return HTMLResponse("<p>Module not found.</p>", status_code=404)
    all_topics = topic_svc.get_all_topics_flat(db)
    return templates.TemplateResponse(
        request, "modules/detail.html",
        {"module": module, "all_topics": all_topics},
    )


@router.post("/{module_id}/topics", response_class=HTMLResponse)
def add_topic_to_module(
    module_id: int,
    request: Request,
    topic_id: int = Form(...),
    db: Session = Depends(get_db),
):
    module_svc.add_topic_to_module(db, module_id=module_id, topic_id=topic_id)
    module = module_svc.get_module(db, module_id)
    all_topics = topic_svc.get_all_topics_flat(db)
    if _is_htmx(request) and module:
        return templates.TemplateResponse(
            request, "partials/module_topics.html",
            {"module": module, "all_topics": all_topics},
        )
    return RedirectResponse(f"/modules/{module_id}", status_code=303)


@router.patch("/topics/{module_topic_id}/status", response_class=HTMLResponse)
def update_module_topic_status(
    module_topic_id: int,
    request: Request,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    module_topic = module_svc.update_module_topic_status(db, module_topic_id=module_topic_id, status=status)
    if _is_htmx(request) and module_topic:
        return templates.TemplateResponse(
            request, "partials/module_topic_row.html",
            {"item": module_topic},
        )
    if module_topic:
        return RedirectResponse(f"/modules/{module_topic.module_id}", status_code=303)
    return HTMLResponse("Not found", status_code=404)


@router.delete("/topics/{module_topic_id}", response_class=HTMLResponse)
def remove_module_topic(module_topic_id: int, request: Request, db: Session = Depends(get_db)):
    module_svc.remove_topic_from_module(db, module_topic_id)
    if _is_htmx(request):
        return HTMLResponse("")
    return RedirectResponse("/modules", status_code=303)


@router.delete("/{module_id}", response_class=HTMLResponse)
def delete_module(module_id: int, request: Request, db: Session = Depends(get_db)):
    module_svc.delete_module(db, module_id)
    if _is_htmx(request):
        return HTMLResponse("")
    return RedirectResponse("/modules", status_code=303)
