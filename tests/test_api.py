"""Pruebas de contrato de FastAPI con un analizador de prueba."""
from fastapi.testclient import TestClient
import pytest

from backend.app.main import create_app
from backend.app.model import SentimentAnalyzer, SentimentResult


class FakeAnalyzer:
    """Sustituto determinista que evita descargar/ejecutar BERTweet en pruebas."""
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail

    def predict(self, text: str) -> SentimentResult:
        if self.should_fail:
            raise RuntimeError("fallo simulado")
        return SentimentResult("Positivo", "POS", 0.91)


def client_for(analyzer: FakeAnalyzer) -> TestClient:
    return TestClient(create_app(analyzer=analyzer))


def test_health_reports_loaded_model() -> None:
    with client_for(FakeAnalyzer()) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "model_loaded": True}


def test_valid_prediction_has_consistent_response() -> None:
    text = "The crew was helpful."
    with client_for(FakeAnalyzer()) as client:
        response = client.post("/predict", json={"text": text})
    assert response.status_code == 200
    assert response.json() == {
        "text": text, "sentiment": "Positivo", "original_label": "POS", "score": 0.91
    }


def test_empty_text_is_rejected() -> None:
    with client_for(FakeAnalyzer()) as client:
        response = client.post("/predict", json={"text": ""})
    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


def test_missing_text_field_has_specific_validation_message() -> None:
    with client_for(FakeAnalyzer()) as client:
        response = client.post("/predict", json={})
    assert response.status_code == 422
    assert response.json()["message"] == "La solicitud debe incluir el campo 'text'."


def test_non_string_text_has_specific_validation_message() -> None:
    with client_for(FakeAnalyzer()) as client:
        response = client.post("/predict", json={"text": 123})
    assert response.status_code == 422
    assert "campo 'text' como texto" in response.json()["message"]


def test_whitespace_text_is_rejected() -> None:
    with client_for(FakeAnalyzer()) as client:
        response = client.post("/predict", json={"text": "   \n  "})
    assert response.status_code == 422
    assert "solo espacios" in response.json()["message"]


def test_too_long_text_is_rejected() -> None:
    with client_for(FakeAnalyzer()) as client:
        response = client.post("/predict", json={"text": "x" * 5_001})
    assert response.status_code == 422
    assert "5000 caracteres" in response.json()["message"]


def test_maximum_allowed_text_length_is_accepted() -> None:
    text = "x" * 5_000
    with client_for(FakeAnalyzer()) as client:
        response = client.post("/predict", json={"text": text})
    assert response.status_code == 200
    assert len(response.json()["text"]) == 5_000


def test_model_error_returns_service_unavailable() -> None:
    with client_for(FakeAnalyzer(should_fail=True)) as client:
        response = client.post("/predict", json={"text": "A valid comment"})
    assert response.status_code == 503
    assert response.json()["error"] == "request_error"


@pytest.mark.parametrize(
    ("original", "expected"),
    [("NEG", "Negativo"), ("NEU", "Neutral"), ("POS", "Positivo")],
)
def test_model_labels_map_to_expected_sentiments(original: str, expected: str) -> None:
    assert SentimentAnalyzer.normalize_label(original) == expected
