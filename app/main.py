from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app import models  # noqa: F401 — registers all models with Base.metadata
from app.routers import topics, exercises, plans, lessons

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Python Learner", docs_url="/api/docs")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(topics.router)
app.include_router(exercises.router)
app.include_router(plans.router)
app.include_router(lessons.router)


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return RedirectResponse("/topics")
