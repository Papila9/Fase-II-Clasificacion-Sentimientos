# Frontend

La interfaz Streamlit presenta el campo de comentario y llama a FastAPI mediante `frontend/api_client.py`. Configura `API_URL` como URL alcanzable desde el proceso frontend (`http://localhost:8000` local o `http://backend:8000` en Compose). No carga el modelo en el frontend.
