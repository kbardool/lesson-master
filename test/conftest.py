"""Shared pytest fixtures: an isolated file-backed SQLite DB per test, plus a
TestClient whose get_db dependency is bound to that same database."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401 — registers all models with Base.metadata
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def engine(tmp_path):
    url = f"sqlite:///{tmp_path / 'test.db'}"
    eng = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    try:
        yield eng
    finally:
        eng.dispose()


@pytest.fixture()
def SessionFactory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture()
def db(SessionFactory):
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(SessionFactory):
    def override_get_db():
        session = SessionFactory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
