"""Integration tests hitting the FastAPI endpoints via TestClient."""

from app.services import module as module_svc
from app.services import subject as subject_svc
from app.services import topic as topic_svc


def test_top_level_pages_render(client):
    for path in ["/subjects", "/modules", "/topics"]:
        resp = client.get(path)
        assert resp.status_code == 200


def test_root_redirects_to_topics(client):
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code in (302, 303, 307)
    assert resp.headers["location"] == "/topics"


def test_create_module_via_api(client):
    resp = client.post("/modules/", data={"name": "Concurrency", "description": "async & threads"})
    assert resp.status_code == 200
    listing = client.get("/modules")
    assert "Concurrency" in listing.text


def test_create_subject_sends_hx_trigger_header(client):
    """
    The create-subject response must carry HX-Trigger: subject-created so the
    client-side form listens for this specific event (rather than the generic
    htmx:afterRequest, which also — unreliably — fires for the "Generate with
    AI" request nested in the same form) to close and reset itself only on an
    actual successful create. Real htmx requests always send HX-Request: true;
    without it the server 303-redirects (no header) to the plain index page.
    """
    resp = client.post(
        "/subjects/",
        data={"name": "Python Advanced Programming", "description": ""},
        headers={"HX-Request": "true"},
    )
    assert resp.status_code == 200
    assert resp.headers.get("hx-trigger") == "subject-created"


def test_generate_description_does_not_send_hx_trigger_header(client):
    resp = client.post(
        "/subjects/generate-description",
        data={"name": "Python Advanced Programming", "description": ""},
    )
    assert resp.status_code == 200
    assert "hx-trigger" not in resp.headers


def test_attach_module_to_subject_via_api(client, db):
    subject = subject_svc.create_subject(db, name="Python Advanced Programming")
    module = module_svc.create_module(db, name="Python Debugging")

    resp = client.post(f"/subjects/{subject.id}/modules", data={"module_id": module.id})
    assert resp.status_code == 200

    detail = client.get(f"/subjects/{subject.id}")
    assert detail.status_code == 200
    assert "Python Debugging" in detail.text


def test_add_topic_to_module_via_api(client, db):
    module = module_svc.create_module(db, name="M")
    topic = topic_svc.create_topic(db, name="Reading tracebacks")

    resp = client.post(f"/modules/{module.id}/topics", data={"topic_id": topic.id})
    assert resp.status_code == 200

    detail = client.get(f"/modules/{module.id}")
    assert "Reading tracebacks" in detail.text
