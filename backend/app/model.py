"""Carga y ejecución del clasificador publicado en Hugging Face."""
from dataclasses import dataclass
from typing import Any

MODEL_ID = "finiteautomata/bertweet-base-sentiment-analysis"
MAX_TOKENS = 128


@dataclass
class SentimentResult:
    """Resultado interno de una predicción."""
    sentiment: str
    original_label: str
    score: float


class SentimentAnalyzer:
    """Mantiene el modelo y tokenizador en memoria mientras vive el backend."""
    def __init__(self, tokenizer: Any, model: Any, id_to_label: dict[int, str]) -> None:
        import torch

        self.tokenizer = tokenizer
        self.model = model
        self.id_to_label = id_to_label
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()

    @classmethod
    def from_pretrained(cls, model_id: str = MODEL_ID) -> "SentimentAnalyzer":
        """Descarga los artefactos públicos y los carga una sola vez."""
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForSequenceClassification.from_pretrained(model_id)
        # El mapeo ya viene dentro del config del checkpoint cargado con el modelo.
        labels = {int(key): str(value) for key, value in model.config.id2label.items()}
        return cls(tokenizer, model, labels)

    @staticmethod
    def normalize_label(original_label: str) -> str:
        """Traduce las etiquetas conocidas del checkpoint al español."""
        labels = {"NEG": "Negativo", "NEU": "Neutral", "POS": "Positivo"}
        normalized = original_label.strip().upper()
        if normalized not in labels:
            raise ValueError(f"Etiqueta no reconocida por el modelo: {original_label}")
        return labels[normalized]

    def predict(self, text: str) -> SentimentResult:
        """Tokeniza el texto sin transformaciones y trunca a 128 tokens."""
        import torch

        encoded = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=MAX_TOKENS)
        encoded = {name: tensor.to(self.device) for name, tensor in encoded.items()}
        with torch.inference_mode():
            logits = self.model(**encoded).logits
            probabilities = torch.softmax(logits, dim=-1)[0]
        class_id = int(torch.argmax(probabilities).item())
        label = self.id_to_label[class_id]
        return SentimentResult(self.normalize_label(label), label, float(probabilities[class_id].item()))
