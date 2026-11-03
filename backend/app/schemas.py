"""Esquemas de solicitudes y respuestas de la API."""
from pydantic import BaseModel, Field, field_validator

MAX_TEXT_CHARACTERS = 5_000


class PredictionRequest(BaseModel):
    """Texto a clasificar."""
    text: str = Field(max_length=MAX_TEXT_CHARACTERS)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("El texto no puede estar vacío ni contener solo espacios.")
        return value


class PredictionResponse(BaseModel):
    """Formato estable para un resultado de inferencia."""
    text: str
    sentiment: str
    original_label: str
    score: float = Field(ge=0, le=1)


class ErrorResponse(BaseModel):
    """Formato uniforme de error."""
    error: str
    message: str
