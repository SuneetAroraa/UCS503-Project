
from unittest.mock import patch

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


def test_rules_mode_includes_evaluation_table():
    response = client.post(
        "/simplify",
        json={
            "text": "The system uses many resources.",
            "mode": "rules",
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["selected_engine"] == "rules"
    assert data["llm_text"] is None
    assert len(data["evaluation_table"]) == 7


def test_llm_mode_uses_gemini_result():
    text = "The system uses many resources."

    with patch(
        "code.python.hybrid_engine.simplify_with_gemini",
        return_value=text,
    ):
        response = client.post(
            "/simplify",
            json={
                "text": text,
                "mode": "llm",
            },
        )

    assert response.status_code == 200

    data = response.json()
    assert data["selected_engine"] == "llm"
    assert data["simplified_text"] == text
    assert data["llm_text"] == text


def test_hybrid_mode_falls_back_when_gemini_fails():
    text = "The system uses many resources."

    with patch(
        "code.python.hybrid_engine.simplify_with_gemini",
        side_effect=RuntimeError("Simulated Gemini failure"),
    ):
        response = client.post(
            "/simplify",
            json={
                "text": text,
                "mode": "hybrid",
            },
        )

    assert response.status_code == 200

    data = response.json()
    assert data["selected_engine"] == "rules"
    assert data["fallback_used"] is True
    assert data["rule_based_text"] == data["simplified_text"]
    assert data["llm_text"] is None


def test_hybrid_mode_falls_back_when_meaning_check_fails():
    text = "The drug is not approved for children."
    candidate = "The drug is approved for children."

    with patch(
        "code.python.hybrid_engine.simplify_with_gemini",
        return_value=candidate,
    ):
        response = client.post(
            "/simplify",
            json={
                "text": text,
                "mode": "hybrid",
            },
        )

    assert response.status_code == 200

    data = response.json()
    assert data["selected_engine"] == "rules"
    assert data["fallback_used"] is True
    assert data["meaning_check"]["safe"] is False
    assert data["rule_based_text"] == data["simplified_text"]


def test_invalid_mode_is_rejected():
    response = client.post(
        "/simplify",
        json={
            "text": "The system uses many resources.",
            "mode": "unsupported",
        },
    )

    assert response.status_code == 422


def test_batch_rules_preserves_input_order_without_gemini():
    texts = [
        "Although the process is complicated, the team can finish it.",
        "The application uses several resources to support its users.",
    ]

    with patch("code.python.api.simplify_many_with_gemini") as gemini:
        response = client.post(
            "/simplify/batch",
            json={"texts": texts, "mode": "rules"},
        )

    assert response.status_code == 200
    data = response.json()
    assert [item["index"] for item in data["results"]] == [0, 1]
    assert [item["mode"] for item in data["results"]] == ["rules", "rules"]
    assert all(item["selected_engine"] == "rules" for item in data["results"])
    gemini.assert_not_called()


def test_batch_gemini_failure_returns_rule_fallback_without_gemini_metrics():
    texts = [
        "Although the process is complicated, the team can finish it.",
        "The application uses several resources to support its users.",
    ]

    with patch(
        "code.python.api.simplify_many_with_gemini",
        side_effect=RuntimeError("daily quota exhausted"),
    ):
        response = client.post(
            "/simplify/batch",
            json={"texts": texts, "mode": "llm"},
        )

    assert response.status_code == 200
    results = response.json()["results"]
    assert [item["index"] for item in results] == [0, 1]
    assert all(item["selected_engine"] == "rules" for item in results)
    assert all(item["fallback_used"] is True for item in results)
    assert all(item["llm_text"] is None for item in results)
    assert all(item["llm_readability"] is None for item in results)


def test_batch_hybrid_rejects_meaning_change_and_uses_rules():
    text = "The treatment is not approved for children under twelve years old."

    with patch(
        "code.python.api.simplify_many_with_gemini",
        return_value=["The treatment is approved for children under twelve years old."],
    ):
        response = client.post(
            "/simplify/batch",
            json={"texts": [text], "mode": "hybrid"},
        )

    assert response.status_code == 200
    item = response.json()["results"][0]
    assert item["selected_engine"] == "rules"
    assert item["fallback_used"] is True
    assert item["meaning_check"]["safe"] is False
    assert item["simplified_text"] == item["rule_based_text"]
