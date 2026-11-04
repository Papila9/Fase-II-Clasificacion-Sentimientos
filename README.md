# Fase II: clasificación de sentimientos con BERTweet

Aplicación académica local que clasifica comentarios mediante el modelo preentrenado `finiteautomata/bertweet-base-sentiment-analysis`. La interfaz Streamlit envía el texto a una API FastAPI; el backend carga Transformers/PyTorch y ejecuta la inferencia. El modelo no se vuelve a entrenar.

> La primera inicialización requiere conexión a Hugging Face para descargar el modelo. El checkpoint está orientado a publicaciones de Twitter en inglés; los resultados funcionales no demuestran su precisión en español ni en otros dominios.

## Arquitectura

```text
Navegador → Streamlit (:8501) → FastAPI (:8000) → tokenizador y modelo BERTweet
```

## Estructura principal

- `backend/`: API, esquemas y módulo de inferencia.
- `frontend/`: aplicación Streamlit y cliente HTTP.
- `tests/`: pruebas automatizadas.
- `docs/`: manual de despliegue en nube y documento de validación.
- `docker-compose.yml`: configuración de ejecución local de los servicios.

## Tecnologías

Python, FastAPI, Uvicorn, Hugging Face Transformers, PyTorch, Streamlit, Docker Compose y pytest. Las versiones se especifican en los archivos `requirements*.txt`.

## Requisitos

- Docker Engine y Docker Compose.
- Conexión a Internet durante la primera carga del modelo.
- Memoria suficiente para PyTorch y BERTweet.
- Para ejecución sin Docker: Python compatible con las dependencias del proyecto.

## Ejecución con Docker

Desde la raíz del repositorio:

```bash
docker compose up --build
```

Abre la interfaz en [http://localhost:8501](http://localhost:8501). La primera descarga del modelo puede tardar.

Para detener los servicios:

```bash
docker compose down
```

La caché del modelo se conserva en el volumen configurado. Para eliminar también los volúmenes:

```bash
docker compose down -v
```

Si necesitas modificar los puertos, utiliza `.env.example` como referencia y crea un archivo `.env` local. No publiques credenciales ni secretos en el repositorio.

## Ejecución local sin Docker

En una terminal, crea y activa un entorno virtual e instala las dependencias:

```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# Linux/macOS:
source .venv/bin/activate

python -m pip install -r requirements.txt
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

En otra terminal, con el entorno activado:

```bash
streamlit run frontend/app.py
```

Si la API se ejecuta en una dirección distinta, configura `API_URL` según la configuración del cliente frontend.

## API

### `GET /health`

Consulta el estado de la API y la disponibilidad del modelo. Cuando el modelo termina de cargar, se espera una respuesta equivalente a:

```json
{
  "status": "ok",
  "model_loaded": true
}
```

### `POST /predict`

Envía un comentario en formato JSON:

```json
{
  "text": "The crew was helpful and kind."
}
```

La respuesta contiene el texto, el sentimiento asignado, la etiqueta original del modelo y la puntuación asociada. Los valores concretos dependen de la inferencia.

Ejemplo de solicitud:

```bash
curl -X POST http://localhost:8000/predict \\
  -H "Content-Type: application/json" \\
  -d '{"text":"The crew was helpful and kind."}'
```

La documentación interactiva de FastAPI está disponible en [http://localhost:8000/docs](http://localhost:8000/docs) cuando el backend está en ejecución.

## Pruebas

Instala las dependencias de desarrollo y ejecuta la suite:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

En la ejecución documentada del 2 de noviembre de 2026 se reportaron **13 pruebas aprobadas y 1 advertencia**. Las pruebas automatizadas utilizan mocks para verificar contratos de API, validaciones y comunicación del cliente; no miden la precisión del modelo.

Además, el documento de validación registra la construcción y ejecución de Docker Compose, la carga del checkpoint, una solicitud real a `/predict` y la visualización de una predicción desde Streamlit. Se trata de una comprobación funcional puntual, no de una evaluación estadística del modelo.

## Limitaciones conocidas

- El modelo está orientado a texto de Twitter en inglés; no se garantiza su desempeño en español ni en otros dominios.
- La puntuación devuelta no debe interpretarse como una medida calibrada de certeza.
- El texto de entrada está sujeto a los límites definidos en la API y al truncamiento del tokenizador.
- Si la caché está vacía y Hugging Face no está disponible, el backend no podrá descargar el modelo.
- El manual de nube describe una estrategia de despliegue; la aplicación no se encuentra publicada en un servicio cloud.

## Documentación

- [Manual de despliegue en la nube (PDF)](docs/Manual_despliegue_nube_Fase_II.pdf)
- [Documento de validación y pruebas (PDF)](docs/Validacion_pruebas_Fase_II_VF.pdf)
