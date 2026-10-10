
from fastapi.testclient import TestClient

from code.python.api import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_simplify_valid_text():
    response = client.post(
        "/simplify",
        json={
            "text": (
                "Although the application requires significant resources, "
                "it provides accessibility features that assist users."
            )
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["simplified_text"]
    assert "original_readability" in data
    assert "simplified_readability" in data
    assert "comparison" in data
    assert "summary" in data


def test_simplify_whitespace_only_text():
    response = client.post(
        "/simplify",
        json={"text": "   "},
    )

    assert response.status_code == 422


def test_simplify_rejects_missing_text():
    response = client.post("/simplify", json={})

    assert response.status_code == 422
