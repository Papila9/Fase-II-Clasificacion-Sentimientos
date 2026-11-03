# Documento de validación y pruebas

## Objetivo

Registrar los casos diseñados para comprobar validaciones, formato de API y comunicación del cliente web con FastAPI, distinguiendo pruebas simuladas de ejecución real con contenedores y modelo.

## Entorno de pruebas

Ejecución observada el 2026-11-02 en Python 3.13.3 con pytest 8.3.4, FastAPI 0.115.6, httpx 0.28.1 y Pydantic 2.14.2. Las pruebas de API usan un analizador falso y no descargan pesos de Hugging Face. La prueba del cliente HTTP simula la respuesta del backend. Docker CLI 29.9.2 y Docker Compose 5.6.1 están instalados. `docker compose config` validó correctamente el archivo. La imagen de ejecución propuesta usa Python 3.11.

## Casos de prueba

| ID | Entrada / acción | Resultado esperado | Resultado observado |
|---|---|---|---|
| API-01 | `GET /health` después del inicio | HTTP 200 e indicador `model_loaded: true` | Pasó con analizador inyectado |
| API-02 | Comentario no vacío | HTTP 200, texto, sentimiento, etiqueta original y puntuación entre 0 y 1 | Pasó con respuesta simulada |
| API-03 | Cadena vacía | HTTP 422 con JSON de error de validación | Pasó |
| API-04 | Campo `text` ausente | HTTP 422 que indica el campo requerido | Pasó |
| API-05 | Valor de `text` que no es cadena | HTTP 422 con mensaje específico | Pasó |
| API-06 | Solo espacios y saltos de línea | HTTP 422 con mensaje claro | Pasó |
| API-07 | Más de 5,000 caracteres | HTTP 422 con mensaje de límite | Pasó |
| API-08 | Exactamente 5,000 caracteres | Solicitud aceptada | Pasó con respuesta simulada |
| API-09 | Error del analizador | HTTP 503 con mensaje general y sin detalles internos | Pasó con excepción simulada |
| WEB-01 | Cliente frontend envía texto | POST al endpoint `/predict`, valida estado y decodifica JSON | Pasó con cliente HTTP simulado |
| LABEL-01 | `NEG`, `NEU`, `POS` | Mapeo a Negativo, Neutral y Positivo | Pasó en prueba unitaria |
| MODEL-01 | Secuencia mayor a 128 tokens | Tokenizador original usa truncamiento a 128 tokens | Pendiente: no se hizo una prueba específica de texto largo |
| DOCKER-01 | Inicio con `docker compose up --build -d` | Servicios inician; interfaz y API responden localmente | Pasó: backend healthy y frontend running |
| MODEL-02 | Inicio del contenedor y carga del checkpoint Hugging Face | Backend informa modelo cargado | Pasó: `GET /health` respondió `model_loaded: true` |
| INFER-01 | POST real en `/predict` | Respuesta del checkpoint con texto, sentimiento, etiqueta y puntuación | Pasó desde el contenedor frontend: HTTP 200, sentimiento `Positivo`, etiqueta `POS`, puntuación `0.9918472766876221` |
| NET-01 | Puerto del frontend publicado en Compose | `127.0.0.1:8501` apunta al puerto 8501 del contenedor | Pasó tras añadir la red bridge `frontend-ingress`; `docker compose ps` muestra `127.0.0.1:8501->8501/tcp` |
| WEB-02 | Uso real de Streamlit contra FastAPI | Interfaz muestra el resultado de la predicción | Pasó en navegador: mostró el texto, `Positivo`, `POS` y `99.2%` |

## Resultados obtenidos

Comando ejecutado: `.venv\\Scripts\\python.exe -m pytest -q -p no:cacheprovider` con el entorno virtual activo.

Resultado automatizado observado el 2026-11-02: **13 passed, 1 warning**. El aviso es una `DeprecationWarning` de Starlette por el alias `anyio.abc.BlockingPortal`. Las pruebas cubren salud, respuesta válida simulada, validaciones de texto, límites, mapeo de etiquetas, excepción simulada del analizador y llamada del cliente HTTP Streamlit.

La ejecución real de Compose construyó las imágenes y arrancó los dos servicios. El backend informó `model_loaded: true`. Se probó desde el contenedor frontend la conectividad a `http://backend:8000/health` (HTTP 200) y se envió una predicción real a `/predict` (HTTP 200; `Positivo`, `POS`, puntuación `0.9918472766876221`). Inicialmente Streamlit no era accesible desde el host: el puerto solicitado no aparecía publicado. Se añadió `frontend-ingress` para conectar el frontend a una red bridge además de `app-internal`; se recreó únicamente el frontend. Después `docker compose ps` reportó `127.0.0.1:8501->8501/tcp`, `http://localhost:8501` respondió HTTP 200 y una clasificación iniciada en el navegador mostró `Positivo`, `POS` y `99.2%`. El backend y el volumen de caché no se recrearon ni eliminaron durante el ajuste de red.

## Casos extremos

Se cubren texto vacío, espacios, campo ausente, tipo incorrecto, límite exacto y exceso de longitud, además de excepción durante inferencia (simulada). Quedan para validación manual Unicode/emojis, textos muy largos con truncamiento por tokens, descarga fallida del Hub y respuesta lenta/interrupción de API.

## Evidencias disponibles

El proyecto incluye casos automatizados; la salida de pytest es evidencia de la ejecución simulada. También se observaron `docker compose config`, `docker compose ps`, los logs de Streamlit y FastAPI, las respuestas HTTP y el resultado visible en el navegador. No se adjuntó una captura al proyecto. Las pruebas unitarias usan un analizador simulado, por lo que no demuestran por sí solas la calidad del modelo; la predicción real es una comprobación funcional puntual, no una evaluación de precisión.

## Conclusiones

La suite del contrato HTTP, la configuración de Compose, la carga del modelo, una predicción real y el flujo desde la interfaz Streamlit se comprobaron. Queda pendiente la prueba específica del truncamiento a 128 tokens con un texto largo y una evaluación sistemática de calidad del modelo; esta ejecución no pretende medir precisión ni generalización.
