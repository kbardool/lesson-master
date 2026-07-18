# lesson-master

A local web app for building and following structured learning curricula, organized as
**Subjects → Modules → Topics → {Lessons, Exercises}**.

## Stack

| Layer     | Choice                              |
|-----------|-------------------------------------|
| Backend   | FastAPI                             |
| ORM       | SQLAlchemy 2.0 (sync, SQLite)       |
| Migrations| Alembic                             |
| Frontend  | HTMX + Jinja2 (no build step)       |
| Packages  | uv                                  |

## Data model

```
Subjects
 └─▶ Modules            (many-to-many: a subject has 0..n modules;
      └─▶ Topics         a module may belong to 0..n subjects)
           ├─▶ Lessons
           └─▶ Exercises
```

| Entity        | Table             | Notes                                             |
|---------------|-------------------|---------------------------------------------------|
| Subject       | `subjects`        | Top of the hierarchy (new)                        |
| Module        | `modules`         | Grouping of topics (formerly "Plan")              |
| —             | `subject_modules` | Many-to-many link between subjects and modules    |
| ModuleTopic   | `module_topics`   | A topic's placement in a module (formerly "PlanItem") |
| Topic         | `topics`          |                                                   |
| Exercise      | `topic_exercises` | Exercises belonging to a topic                    |
| TopicLesson   | `topic_lessons`   | Per-level lesson content for a topic              |

## Setup

```bash
# Install dependencies
uv sync

# Apply migrations (creates ./data/lesson_master.db with the full schema)
alembic upgrade head

# Populate the database from the JSON snapshot (defaults to v2.0)
python utils/seed_database.py

# Run the dev server
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000 — you'll land on the Topics page. The sidebar links to
**Subjects**, **Modules**, and **Topics**.

## Project structure

```
app/
  main.py          # FastAPI app, Jinja2 filters, router registration
  database.py      # Engine, SessionLocal, Base, get_db() dependency (DB in ./data)
  models/          # SQLAlchemy models (Subject, Module, ModuleTopic, Topic, Exercise, ExerciseAttempt, TopicLesson)
  services/        # Business logic (no HTTP concerns — easy to test)
  routers/         # FastAPI routers (thin: validate input, call service, render template)
  templates/
    base.html      # Sidebar layout, HTMX script
    subjects/      # Subjects list + detail (attached modules)
    modules/       # Modules list + detail (module topics)
    topics/        # Topics list + detail
    exercises/     # Exercise detail + attempt form
    partials/      # HTMX swap targets (topic_list, module_list, module_topics, subject_modules, ...)
static/
  app.css          # All styles — dark editor theme, CSS variables
data/
  lesson_master.db # SQLite database (generated; gitignored)
alembic/
  env.py           # Configured to find all models automatically
  versions/        # Migrations, incl. the subjects/modules schema change
utils/
  seed_data_v2.0.json # Snapshot of the current (v2.0) schema — subjects/modules/...
  seed_data_v1.0.json # Snapshot of the original (v1.0) schema — learning_plans/plan_items/...
  seed_database.py    # Loads a versioned snapshot into an empty (matching-schema) database
test/
  test_models.py   # Unit tests for the schema + Subject↔Module relationship
  test_services.py # Unit tests for the module/subject service layers
  test_api.py      # Integration tests hitting the FastAPI endpoints
  test_seed.py     # Verifies the JSON seed loader
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

## Running the tests

```bash
uv run pytest
```

## Adding a migration

```bash
# After changing a model
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## What changed in this release

This project was generalized from the Python-specific **python-learner** into
**lesson-master**:

- **Renamed** the app, and moved the database to `./data/lesson_master.db`.
- **Introduced the `Subject` entity** at the top of the hierarchy, with a many-to-many
  relationship to modules (`subject_modules`). The seed data includes a
  *"Python Advanced Programming"* subject linked to the existing *"Python Debugging"* module.
- **Renamed the `Plan` entity to `Module`** and its tables accordingly:
  `learning_plans → modules`, `plan_items → module_topics`, `exercises → topic_exercises`.
  The UI (routes, templates, nav, styles) was renamed to match, and a **Subjects** section
  was added.
- **Added an Alembic migration** capturing the schema change (renames + new `subjects` /
  `subject_modules` tables). The initial migration was also completed to create `topic_lessons`
  (previously only created by `create_all`), so revision `623ae4287a2d` is now a faithful v1.0
  schema and `alembic upgrade 623ae4287a2d` reproduces the original database exactly.
- **Replaced** the ad-hoc `seed_debugging_plan.py` with `utils/seed_database.py`, which loads a
  portable, versioned JSON snapshot into a freshly migrated database. Two snapshots ship:
  `seed_data_v2.0.json` (current schema) and `seed_data_v1.0.json` (original schema). Pick one
  with `--version {1.0,2.0}` / `--input <file>`, and target a specific DB with `--database`:

  ```bash
  # Seed the current v2.0 database (default)
  alembic upgrade head
  python utils/seed_database.py

  # Reproduce & seed an original v1.0 database (on a fresh, empty data/ dir)
  alembic upgrade 623ae4287a2d           # stop at the v1.0 schema revision
  python utils/seed_database.py --version 1.0

  # ...or seed any existing v1.0-schema database directly:
  python utils/seed_database.py --version 1.0 --database /path/to/v1.db
  ```
- **Added a pytest suite** under `test/` covering models, services, API, and seeding.

## Roadmap

- [ ] Phase 1 ✓ — Topic tree, modules, subjects, progress tracking
- [ ] Phase 2 — CodeMirror editor in-browser, attempt diff view
- [ ] Phase 3 — Dashboard, tag filtering, Markdown export
- [ ] Phase 4 — AI-assisted exercise hints (Anthropic API)
