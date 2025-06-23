from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

def test_templates_route():
    resp = client.get("/templates")
    assert resp.status_code == 200

def test_transcribe_missing_file():
    resp = client.post("/transcribe")
    assert resp.status_code == 422  # validation error for missing fields 