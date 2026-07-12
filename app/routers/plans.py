from typing import Optional

from app.templating import templates
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import plan as plan_svc
from app.services import topic as topic_svc

router = APIRouter(prefix="/plans", tags=["plans"])


def _is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


@router.get("/", response_class=HTMLResponse)
def plans_index(request: Request, db: Session = Depends(get_db)):
    plans = plan_svc.get_all_plans(db)
    return templates.TemplateResponse(
        request, "plans/index.html",
        {"plans": plans},
    )


@router.post("/", response_class=HTMLResponse)
def create_plan(
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    plan_svc.create_plan(db, name=name, description=description or None)
    plans = plan_svc.get_all_plans(db)
    if _is_htmx(request):
        return templates.TemplateResponse(
            request, "partials/plan_list.html",
            {"plans": plans},
        )
    return RedirectResponse("/plans", status_code=303)


@router.get("/{plan_id}", response_class=HTMLResponse)
def plan_detail(plan_id: int, request: Request, db: Session = Depends(get_db)):
    plan = plan_svc.get_plan(db, plan_id)
    if not plan:
        return HTMLResponse("<p>Plan not found.</p>", status_code=404)
    all_topics = topic_svc.get_all_topics_flat(db)
    return templates.TemplateResponse(
        request, "plans/detail.html",
        {"plan": plan, "all_topics": all_topics},
    )


@router.post("/{plan_id}/items", response_class=HTMLResponse)
def add_topic_to_plan(
    plan_id: int,
    request: Request,
    topic_id: int = Form(...),
    db: Session = Depends(get_db),
):
    plan_svc.add_topic_to_plan(db, plan_id=plan_id, topic_id=topic_id)
    plan = plan_svc.get_plan(db, plan_id)
    all_topics = topic_svc.get_all_topics_flat(db)
    if _is_htmx(request) and plan:
        return templates.TemplateResponse(
            request, "partials/plan_items.html",
            {"plan": plan, "all_topics": all_topics},
        )
    return RedirectResponse(f"/plans/{plan_id}", status_code=303)


@router.patch("/items/{item_id}/status", response_class=HTMLResponse)
def update_item_status(
    item_id: int,
    request: Request,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    item = plan_svc.update_item_status(db, item_id=item_id, status=status)
    if _is_htmx(request) and item:
        return templates.TemplateResponse(
            request, "partials/plan_item_row.html",
            {"item": item},
        )
    if item:
        return RedirectResponse(f"/plans/{item.plan_id}", status_code=303)
    return HTMLResponse("Not found", status_code=404)


@router.delete("/items/{item_id}", response_class=HTMLResponse)
def remove_plan_item(item_id: int, request: Request, db: Session = Depends(get_db)):
    plan_svc.remove_item_from_plan(db, item_id)
    if _is_htmx(request):
        return HTMLResponse("")
    return RedirectResponse("/plans", status_code=303)


@router.delete("/{plan_id}", response_class=HTMLResponse)
def delete_plan(plan_id: int, request: Request, db: Session = Depends(get_db)):
    plan_svc.delete_plan(db, plan_id)
    if _is_htmx(request):
        return HTMLResponse("")
    return RedirectResponse("/plans", status_code=303)
