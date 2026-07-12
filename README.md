# python-learner

A local web app for building and following structured Python learning curricula.

## Stack

| Layer     | Choice                              |
|-----------|-------------------------------------|
| Backend   | FastAPI                             |
| ORM       | SQLAlchemy 2.0 (sync, SQLite)       |
| Migrations| Alembic                             |
| Frontend  | HTMX + Jinja2 (no build step)       |
| Packages  | uv                                  |

## Setup

```bash
# Install dependencies
uv sync

# Apply migrations (creates python_learner.db)
alembic upgrade head

# Run the dev server
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000 — you'll land on the Topics page.

## Project structure

```
app/
  main.py          # FastAPI app, Jinja2 filters, router registration
  database.py      # Engine, SessionLocal, Base, get_db() dependency
  models/          # SQLAlchemy models (Topic, Exercise, ExerciseAttempt, LearningPlan, PlanItem)
  services/        # Business logic (no HTTP concerns — easy to test)
  routers/         # FastAPI routers (thin: validate input, call service, render template)
  templates/
    base.html      # Sidebar layout, HTMX script
    topics/        # Topics list + detail
    exercises/     # Exercise detail + attempt form
    plans/         # Plan list + detail
    partials/      # HTMX swap targets (topic_list, exercise_list, plan_items, ...)
static/
  app.css          # All styles — dark editor theme, CSS variables
alembic/
  env.py           # Configured to find all models automatically
```

## HTMX pattern

Most mutating forms return a **partial template** when the `HX-Request` header is present,
swapping only the affected DOM region. Full-page responses are returned for non-HTMX
requests (e.g. direct navigation or JavaScript disabled).

```python
if request.headers.get("HX-Request") == "true":
    return templates.TemplateResponse("partials/topic_list.html", ctx)
return RedirectResponse("/topics", status_code=303)
```

## Adding a migration

```bash
# After changing a model
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Roadmap

- [ ] Phase 1 ✓ — Topic tree, learning plans, progress tracking
- [ ] Phase 2 — CodeMirror editor in-browser, attempt diff view
- [ ] Phase 3 — Dashboard, tag filtering, Markdown export
- [ ] Phase 4 — AI-assisted exercise hints (Anthropic API)
