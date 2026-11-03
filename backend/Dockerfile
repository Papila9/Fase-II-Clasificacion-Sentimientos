FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/home/app/.cache/huggingface

WORKDIR /app
COPY backend/requirements.txt ./requirements.txt

# Instala la versión CPU de PyTorch; la aplicación no necesita CUDA en Docker.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.5.1 && \
    pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
RUN useradd --create-home --uid 10001 appuser && \
    mkdir -p /home/app/.cache/huggingface && \
    chown -R appuser:appuser /app /home/app/.cache

USER appuser
EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
