# Backend

FastAPI expone `GET /health` y `POST /predict`. El módulo `app/model.py` carga una vez el tokenizador y checkpoint BERTweet al arrancar, con inferencia directa y truncamiento a 128 tokens. Para desarrollo local desde la raíz: `python -m uvicorn backend.app.main:app --reload --port 8000` (requiere instalar `backend/requirements.txt`). La descarga inicial requiere conexión a Hugging Face.
