# Fase II: clasificación de sentimientos con BERTweet

Aplicación académica local que clasifica comentarios con el modelo público `finiteautomata/bertweet-base-sentiment-analysis`. Streamlit envía texto a una API FastAPI; solo el backend carga Transformers/PyTorch y ejecuta inferencia. El modelo no se vuelve a entrenar.

> La primera inicialización necesita conexión a Hugging Face para descargar el modelo. El checkpoint fue preparado para texto de Twitter en inglés; estos resultados no validan por sí solos otros idiomas o dominios.

## Arquitectura

```text
Navegador → Streamlit (:8501) → FastAPI (:8000) → tokenizador y modelo BERTweet
                                  └── red de salida para descargar de Hugging Face
```

Streamlit y FastAPI comparten la red privada `app-internal`. Streamlit también se conecta a `frontend-ingress`, una red bridge que permite a Docker Desktop publicar la interfaz en `localhost:8501`; FastAPI no se conecta a esa red. El backend usa `model-egress` para descargar el modelo y conserva la caché en un volumen. La API se publica solo en `127.0.0.1:8000` para pruebas locales.

## Estructura

```text
backend/app/       API, esquemas y módulo de inferencia
frontend/          aplicación Streamlit y cliente HTTP
tests/             pruebas unitarias con mocks
scripts/           pruebas extremas contra la API real (pruebas_extremas.py)
docs/              manual de despliegue en nube y documentos de validación (Word/Markdown)
docker-compose.yml ejecución local de los dos servicios
```

## Tecnologías

Python 3.11, FastAPI, Uvicorn, Hugging Face Transformers, PyTorch, Streamlit, Docker Compose y pytest. Se usan versiones fijadas en los archivos `requirements.txt`.

## Requisitos

- Docker Engine y Docker Compose v2.33.1 o posterior (se usa prioridad de gateway para dar salida al backend sin abrir la red frontend/backend).
- O Python 3.11 para ejecución directa.
- Conexión a Internet en la primera carga de BERTweet.
- Memoria suficiente para PyTorch y el modelo. La inferencia configurada es CPU; no se ha medido consumo ni latencia en este entorno.

## Ejecución con Docker

Desde la raíz:

```bash
docker compose up --build
```

Abre `http://localhost:8501`. La primera descarga puede tardar. Detén con `Ctrl+C` y `docker compose down`; la caché permanece en el volumen `huggingface-cache`. Para eliminarla explícitamente: `docker compose down -v`.

Para cambiar puertos, copia `.env.example` a `.env` y ajusta `FRONTEND_PORT` o `BACKEND_PORT`. No agregues credenciales al repositorio.

## Ejecución local sin Docker

En una terminal instala e inicia el backend:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

En otra terminal, con el mismo entorno activado:

```bash
streamlit run frontend/app.py
```

La aplicación usa `http://localhost:8000` por defecto; cambia `API_URL` si ejecutas el backend en otra dirección. Las instrucciones anteriores son comandos propuestos; la ejecución debe validarse en un equipo con dependencias disponibles.

## API

### `GET /health`

Respuesta prevista tras la carga del modelo:

```json
{"status":"ok","model_loaded":true}
```

### `POST /predict`

Entrada JSON; admite texto no vacío de hasta 5,000 caracteres:

```json
{"text":"The crew was helpful and kind."}
```

Respuesta:

```json
{
  "text":"The crew was helpful and kind.",
  "sentiment":"Positivo",
  "original_label":"POS",
  "score":0.91
}
```

Los valores de respuesta son ilustrativos del **formato**, no resultados de una inferencia real. Errores de validación usan HTTP 422 y errores de inferencia HTTP 503 con `{"error":"...","message":"..."}`.

Ejemplo de solicitud:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"The crew was helpful and kind."}'
```

FastAPI ofrece documentación interactiva en `http://localhost:8000/docs`.

## Pruebas

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

La suite usa un analizador simulado para verificar los contratos y no mide el rendimiento ni la precisión del modelo. El 2026-11-03 se ejecutó con 13 aprobadas y 1 warning de deprecación. También se validaron Compose, la carga del modelo, una predicción real y la interacción desde Streamlit. Ese día se enviaron 23 casos extremos a la API real en Docker y los 23 códigos HTTP coincidieron con lo esperado. El informe de salida está en [resultados_pruebas_extremas.md](resultados_pruebas_extremas.md); la suite simulada y la comprobación real están diferenciadas en la documentación de validación.

### Pruebas extremas contra el modelo real

Con los contenedores en ejecución (`docker compose up --build`), en otra terminal:

```bash
python scripts/pruebas_extremas.py
```

El script usa solo la biblioteca estándar y envía a `http://localhost:8000` casos de inglés, español, emojis, sarcasmo, texto largo e inválidos. El backend configura truncamiento a 128 tokens; esta batería verifica la respuesta HTTP ante el texto largo, pero no inspecciona directamente la cantidad de tokens procesados. La ejecución documentada produjo 23 respuestas con el código HTTP esperado. Los resultados están en [resultados_pruebas_extremas.md](resultados_pruebas_extremas.md). Usa `--api-url` para otra dirección y `--salida resultados.md` para guardar la tabla.

## Limitaciones

- El modelo se entrenó para publicaciones de Twitter en inglés; no se garantiza su rendimiento en otras fuentes ni en español. La ficha del modelo limita su uso a investigación científica y usos no comerciales ([ficha de Hugging Face](https://huggingface.co/finiteautomata/bertweet-base-sentiment-analysis)).
- La puntuación es la probabilidad softmax de la clase predicha, no una medida calibrada de certeza.
- Se limita el texto a 5,000 caracteres y el tokenizador trunca a 128 tokens.
- Si Hugging Face no está disponible durante una caché vacía, el backend no inicia.
- Las pruebas simuladas comprueban API/cliente, no la clasificación del checkpoint.
- El manual de nube es una estrategia futura; no se ha desplegado nada.

## Documentos

- [Manual de despliegue en la nube (Word, corregido)](docs/Manual-despliegue-nube_corregido.docx)
- [Manual de despliegue en la nube (Markdown)](docs/despliegue-nube.md)
- [Documento institucional de validación actualizado (Word)](docs/Validacion_pruebas_Fase_II_UV_actualizado.docx)
- [Script de pruebas extremas](scripts/pruebas_extremas.py)
- [Registro de validación actualizado (Markdown)](docs/validacion-y-pruebas.md)
- [Resultados completos de las pruebas extremas (Markdown)](resultados_pruebas_extremas.md)
