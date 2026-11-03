"""Interfaz Streamlit; toda inferencia ocurre en la API FastAPI."""
import os

import requests
import streamlit as st

from api_client import request_prediction

API_URL = os.getenv("API_URL", "http://localhost:8000")
MAX_TEXT_CHARACTERS = 5_000

st.set_page_config(page_title="Sentimientos con BERTweet", page_icon="💬", layout="centered")
st.title("Clasificador de sentimientos")
st.markdown(
    "Escribe un comentario y consulta su clasificación con **BERTweet**. "
    "El texto se envía a una API local para su análisis."
)
text = st.text_area(
    "Comentario",
    placeholder="Por ejemplo: The flight was delayed, but the crew was very helpful.",
    height=150,
    max_chars=MAX_TEXT_CHARACTERS,
    help=f"Máximo {MAX_TEXT_CHARACTERS:,} caracteres.",
)

if st.button("Clasificar sentimiento", type="primary", use_container_width=True):
    if not text.strip():
        st.warning("Escribe un comentario antes de ejecutar la clasificación.")
    elif len(text) > MAX_TEXT_CHARACTERS:
        st.error(f"El comentario supera el máximo de {MAX_TEXT_CHARACTERS:,} caracteres.")
    else:
        try:
            result = request_prediction(API_URL, text)
            st.subheader("Resultado")
            st.write("**Texto analizado:**", result["text"])
            st.success(f"Sentimiento detectado: {result['sentiment']}")
            st.write(f"**Etiqueta original:** `{result['original_label']}`")
            st.metric("Puntuación del modelo", f"{result['score']:.1%}")
        except requests.exceptions.Timeout:
            st.error("El backend tardó demasiado en responder. Intenta de nuevo.")
        except requests.exceptions.ConnectionError:
            st.error("No se pudo conectar con la API. Verifica que el backend esté iniciado.")
        except requests.exceptions.HTTPError as exc:
            try:
                message = exc.response.json().get("message", "La API rechazó la solicitud.")
            except (ValueError, AttributeError):
                message = "La API rechazó la solicitud."
            st.error(message)
        except requests.exceptions.RequestException:
            st.error("Ocurrió un error de comunicación con la API.")

st.caption(f"Modelo: finiteautomata/bertweet-base-sentiment-analysis · API: {API_URL}")
