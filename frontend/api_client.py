"""Cliente HTTP pequeño para que Streamlit no cargue el modelo."""
import requests


def request_prediction(api_url: str, text: str, timeout: float = 60.0) -> dict:
    """Envía el texto al backend y devuelve su respuesta JSON."""
    response = requests.post(f"{api_url.rstrip('/')}/predict", json={"text": text}, timeout=timeout)
    response.raise_for_status()
    return response.json()
