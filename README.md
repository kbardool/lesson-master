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

# (Optional) enable AI-assisted generation — see "Configuring the Anthropic API key" below
cp .env.example .env && $EDITOR .env

# Run the dev server
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000 — you'll land on the Topics page. The sidebar links to
**Subjects**, **Modules**, and **Topics**.

### Configuring the Anthropic API key

The AI-assisted features (lesson/exercise generation, subject description generation) call
the Anthropic API and require `ANTHROPIC_API_KEY`. The suggested method for local dev is a
`.env` file, loaded automatically at startup via `python-dotenv`:

```bash
cp .env.example .env
# then edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```

`.env` is gitignored, so your key never gets committed. This is loaded once, at process
start (`app/main.py`) — it covers running the app via `uvicorn`, but **not** one-off scripts
like `utils/seed_database.py` or `alembic`, which don't need the key anyway. If you'd rather
not use a `.env` file, exporting the variable in your shell works the same way:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Project structure

```
app/
  main.py          # FastAPI app, Jinja2 filters, router registration
  database.py      # Engine, SessionLocal, Base, get_db() dependency (DB in ./data)
  models/          # SQLAlchemy models (Subject, Module, ModuleTopic, Topic, Exercise, ExerciseAttempt, TopicLesson)
  services/        # Business logic (no HTTP concerns — easy to test), incl. ai.py (LLM calls)
  routers/         # FastAPI routers (thin: validate input, call service, render template)
  templates/
    base.html      # Sidebar layout, HTMX script
    subjects/      # Subjects list + detail (attached modules)
    modules/       # Modules list + detail (module topics)
    topics/        # Topics list + detail
    exercises/     # Exercise detail + attempt form
    partials/      # HTMX swap targets (topic_list, module_list, subject_description_field, ...)
static/
  app.css          # All styles — dark editor theme, CSS variables
data/
  lesson_master.db # SQLite database (generated; gitignored)
backups/
  backup_*.json    # Generated database backups (see utils/backup_database.py; gitignored)
alembic/
  env.py           # Configured to find all models automatically
  versions/        # Migrations, incl. the subjects/modules schema change
utils/
  seed_data_v2.0.json # Snapshot of the current (v2.0) schema — subjects/modules/...
  seed_data_v1.0.json # Snapshot of the original (v1.0) schema — learning_plans/plan_items/...
  seed_database.py    # Loads a versioned snapshot into an empty (matching-schema) database
  backup_database.py  # Dumps the live database to a seed_database-compatible JSON snapshot
test/
  test_models.py             # Unit tests for the schema + Subject↔Module relationship
  test_services.py           # Unit tests for the module/subject service layers
  test_api.py                # Integration tests hitting the FastAPI endpoints
  test_seed.py                # Verifies the JSON seed loader
  test_subject_generation.py  # AI subject-description generation (unit + endpoint)
  test_backup_database.py     # Backup dump correctness + round-trip through the seed loader
ctrf.json          # CTRF test report, regenerated by every `pytest` run (gitignored)
```

## AI-assisted subject descriptions

When creating a new subject, click **✨ Generate with AI** next to the Description field.
It sends the Subject Name (and whatever draft description you've typed, if any) to Claude
and fills the field with a generated description of **60 words or fewer**. This only happens
while the subject is being created — like modules and topics, a subject's description isn't
regenerated after it's saved. Requires `ANTHROPIC_API_KEY` to be set in the environment.

## Backing up the database

```bash
# Back up the current database to backups/backup_<timestamp>.json
python utils/backup_database.py

# Restore it into a freshly migrated (empty) database
alembic upgrade head
python utils/seed_database.py --input backups/backup_<timestamp>.json
```

`backup_database.py` writes every table in FK-safe order, preserving primary keys, foreign
keys, and timestamps exactly as stored, so the output is a drop-in input for
`seed_database.py` (`--database`/`--output` flags let you target a non-default DB or path).

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

Every run also writes `ctrf.json` — a [CTRF](https://ctrf.io)-format test report (via the
`pytest-json-ctrf` plugin, configured through `addopts` in `pyproject.toml`) — for consumption
by CI dashboards or other CTRF-aware tooling.

## Adding a migration

```bash
# After changing a model
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Seeding a specific schema version

`utils/seed_database.py` loads a portable, versioned JSON snapshot into a freshly migrated
database. Two snapshots ship: `seed_data_v2.0.json` (current schema) and `seed_data_v1.0.json`
(original schema). Pick one with `--version {1.0,2.0}` / `--input <file>`, and target a specific
DB with `--database`:

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

## Changes

| Version | Date       | Description |
|---------|------------|--------------|
| 0.1.0   | 2026-07-12 | Initial commit: FastAPI + SQLAlchemy + HTMX app for tracking a Python learning curriculum (Topics, Learning Plans, Exercises, AI-assisted lesson/exercise generation). |
| 0.1.1   | 2026-07-17 | Added the `python_learner.db` SQLite database to the repo. |
| 0.2.0   | 2026-07-17 | Renamed the project to lesson-master; introduced the Subjects → Modules → Topics hierarchy (new `Subject` entity, `Plan` → `Module` rename), an Alembic migration, versioned JSON seed data, and a pytest suite. |
| 0.2.1   | 2026-07-17 | Added GitHub Actions workflows that email on push and on PR-opened. |
| 0.3.0   | 2026-07-22 | Added AI-assisted subject description generation, `utils/backup_database.py` (JSON backup/restore), CTRF pytest reporting, and this Changes table. |

## Roadmap

- [ ] Phase 1 ✓ — Topic tree, modules, subjects, progress tracking
- [ ] Phase 2 — CodeMirror editor in-browser, attempt diff view
- [ ] Phase 3 — Dashboard, tag filtering, Markdown export
- [ ] Phase 4 — AI-assisted exercise hints (Anthropic API)
