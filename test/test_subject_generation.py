"""Tests for AI-assisted subject description generation."""

from unittest.mock import MagicMock

import pytest

from app.services import ai as ai_svc


def _fake_client(text: str) -> MagicMock:
    message = MagicMock()
    message.content = [MagicMock(text=text)]
    client = MagicMock()
    client.messages.create.return_value = message
    return client


def test_generate_subject_description_uses_name_and_draft(monkeypatch):
    client = _fake_client("A focused subject on advanced Python internals.")
    monkeypatch.setattr(ai_svc, "_get_client", lambda: client)

    result = ai_svc.generate_subject_description(
        name="Python Advanced Programming",
        description="covers memory and concurrency",
    )

    assert result == "A focused subject on advanced Python internals."
    prompt = client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "Python Advanced Programming" in prompt
    assert "covers memory and concurrency" in prompt


def test_generate_subject_description_without_draft(monkeypatch):
    client = _fake_client("A subject about testing.")
    monkeypatch.setattr(ai_svc, "_get_client", lambda: client)

    result = ai_svc.generate_subject_description(name="Testing & QA")
    assert result == "A subject about testing."
    prompt = client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "Testing & QA" in prompt


def test_generate_subject_description_truncates_to_60_words(monkeypatch):
    long_text = " ".join(f"word{i}" for i in range(100))
    client = _fake_client(long_text)
    monkeypatch.setattr(ai_svc, "_get_client", lambda: client)

    result = ai_svc.generate_subject_description(name="X")

    words = result.rstrip("…").split()
    assert len(words) <= 60
    assert result.endswith("…")


def test_generate_subject_description_short_text_untouched(monkeypatch):
    client = _fake_client("Short description.")
    monkeypatch.setattr(ai_svc, "_get_client", lambda: client)

    result = ai_svc.generate_subject_description(name="X")
    assert result == "Short description."


def test_generate_description_endpoint_success(client, monkeypatch):
    fake = _fake_client("Generated subject description text.")
    monkeypatch.setattr(ai_svc, "_get_client", lambda: fake)

    resp = client.post(
        "/subjects/generate-description",
        data={"name": "Python Advanced Programming", "description": ""},
    )
    assert resp.status_code == 200
    assert "Generated subject description text." in resp.text
    assert 'id="subject-description-field"' in resp.text


def test_generate_description_endpoint_requires_name(client, monkeypatch):
    fake = _fake_client("should not be used")
    monkeypatch.setattr(ai_svc, "_get_client", lambda: fake)

    resp = client.post("/subjects/generate-description", data={"name": "   ", "description": ""})
    assert resp.status_code == 200
    assert "Enter a subject name" in resp.text
    fake.messages.create.assert_not_called()


def test_generate_description_endpoint_surfaces_missing_api_key(client, monkeypatch):
    def _raise():
        raise EnvironmentError("ANTHROPIC_API_KEY is not set.")

    monkeypatch.setattr(ai_svc, "_get_client", _raise)

    resp = client.post(
        "/subjects/generate-description",
        data={"name": "Python Advanced Programming", "description": ""},
    )
    assert resp.status_code == 200
    assert "ANTHROPIC_API_KEY" in resp.text
