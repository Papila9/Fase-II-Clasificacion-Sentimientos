"""Prueba de integración ligera entre cliente Streamlit y contrato HTTP."""
from unittest.mock import Mock, patch

from frontend.api_client import request_prediction


def test_frontend_client_posts_to_prediction_endpoint() -> None:
    fake_response = Mock()
    fake_response.json.return_value = {"sentiment": "Neutral", "score": 0.72}
    with patch("frontend.api_client.requests.post", return_value=fake_response) as post:
        result = request_prediction("http://backend:8000/", "The flight was okay")
    post.assert_called_once_with(
        "http://backend:8000/predict", json={"text": "The flight was okay"}, timeout=60.0
    )
    fake_response.raise_for_status.assert_called_once()
    assert result["sentiment"] == "Neutral"
