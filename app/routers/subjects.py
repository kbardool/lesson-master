from typing import Optional

from app.templating import templates
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import subject as subject_svc
from app.services import module as module_svc

router = APIRouter(prefix="/subjects", tags=["subjects"])


def _is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


@router.get("/", response_class=HTMLResponse)
def subjects_index(request: Request, db: Session = Depends(get_db)):
    subjects = subject_svc.get_all_subjects(db)
    return templates.TemplateResponse(
        request, "subjects/index.html",
        {"subjects": subjects},
    )


@router.post("/", response_class=HTMLResponse)
def create_subject(
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    subject_svc.create_subject(db, name=name, description=description or None)
    subjects = subject_svc.get_all_subjects(db)
    if _is_htmx(request):
        return templates.TemplateResponse(
            request, "partials/subject_list.html",
            {"subjects": subjects},
        )
    return RedirectResponse("/subjects", status_code=303)


@router.get("/{subject_id}", response_class=HTMLResponse)
def subject_detail(subject_id: int, request: Request, db: Session = Depends(get_db)):
    subject = subject_svc.get_subject(db, subject_id)
    if not subject:
        return HTMLResponse("<p>Subject not found.</p>", status_code=404)
    all_modules = module_svc.get_all_modules(db)
    return templates.TemplateResponse(
        request, "subjects/detail.html",
        {"subject": subject, "all_modules": all_modules},
    )


@router.post("/{subject_id}/modules", response_class=HTMLResponse)
def attach_module(
    subject_id: int,
    request: Request,
    module_id: int = Form(...),
    db: Session = Depends(get_db),
):
    subject_svc.attach_module_to_subject(db, subject_id=subject_id, module_id=module_id)
    subject = subject_svc.get_subject(db, subject_id)
    all_modules = module_svc.get_all_modules(db)
    if _is_htmx(request) and subject:
        return templates.TemplateResponse(
            request, "partials/subject_modules.html",
            {"subject": subject, "all_modules": all_modules},
        )
    return RedirectResponse(f"/subjects/{subject_id}", status_code=303)


@router.delete("/{subject_id}/modules/{module_id}", response_class=HTMLResponse)
def detach_module(
    subject_id: int,
    module_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    subject_svc.detach_module_from_subject(db, subject_id=subject_id, module_id=module_id)
    subject = subject_svc.get_subject(db, subject_id)
    all_modules = module_svc.get_all_modules(db)
    if _is_htmx(request) and subject:
        return templates.TemplateResponse(
            request, "partials/subject_modules.html",
            {"subject": subject, "all_modules": all_modules},
        )
    return RedirectResponse(f"/subjects/{subject_id}", status_code=303)


@router.delete("/{subject_id}", response_class=HTMLResponse)
def delete_subject(subject_id: int, request: Request, db: Session = Depends(get_db)):
    subject_svc.delete_subject(db, subject_id)
    if _is_htmx(request):
        return HTMLResponse("")
    return RedirectResponse("/subjects", status_code=303)
