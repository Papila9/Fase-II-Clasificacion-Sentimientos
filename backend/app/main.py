"""Punto de entrada y endpoints de FastAPI."""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.app.model import SentimentAnalyzer
from backend.app.schemas import ErrorResponse, PredictionRequest, PredictionResponse


def create_app(analyzer: SentimentAnalyzer | None = None) -> FastAPI:
    """Crea la API; permite inyectar un modelo falso en pruebas."""
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if analyzer is None:
            try:
                app.state.analyzer = SentimentAnalyzer.from_pretrained()
            except Exception as exc:
                raise RuntimeError("No fue posible cargar el modelo BERTweet.") from exc
        else:
            app.state.analyzer = analyzer
        yield

    app = FastAPI(
        title="API de análisis de sentimientos con BERTweet",
        version="1.0.0",
        description="Clasificación con finiteautomata/bertweet-base-sentiment-analysis.",
        lifespan=lifespan,
    )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = exc.errors()
        if any(error.get("type") == "string_too_long" for error in errors):
            message = "El texto supera el máximo permitido de 5000 caracteres."
        elif any(error.get("type") == "value_error" for error in errors):
            message = "El texto no puede estar vacío ni contener solo espacios."
        elif any(error.get("type") == "missing" for error in errors):
            message = "La solicitud debe incluir el campo 'text'."
        else:
            message = "Solicitud inválida. Envía un JSON con el campo 'text' como texto."
        body = ErrorResponse(error="validation_error", message=message).model_dump()
        return JSONResponse(status_code=422, content=body)

    @app.exception_handler(HTTPException)
    async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
        body = ErrorResponse(error="request_error", message=str(exc.detail)).model_dump()
        return JSONResponse(status_code=exc.status_code, content=body, headers=exc.headers)

    @app.get("/health")
    async def health(request: Request) -> dict[str, str | bool]:
        """Comprueba la API e informa si el modelo se cargó."""
        return {"status": "ok", "model_loaded": hasattr(request.app.state, "analyzer")}

    @app.post("/predict", response_model=PredictionResponse, responses={
        422: {"model": ErrorResponse}, 503: {"model": ErrorResponse}
    })
    def predict(payload: PredictionRequest, request: Request) -> PredictionResponse:
        """Clasifica un comentario y devuelve etiqueta y puntuación."""
        try:
            result = request.app.state.analyzer.predict(payload.text)
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail="El modelo no pudo procesar el texto. Intenta de nuevo más tarde.",
            ) from exc
        return PredictionResponse(
            text=payload.text,
            sentiment=result.sentiment,
            original_label=result.original_label,
            score=result.score,
        )

    return app


app = create_app()
