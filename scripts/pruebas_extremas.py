"""Pruebas extremas contra la API FastAPI en ejecución.

Uso (con `docker compose up --build` ya corriendo):

    python scripts/pruebas_extremas.py
    python scripts/pruebas_extremas.py --api-url http://localhost:8000 --salida resultados.md

Solo usa la biblioteca estándar. Imprime una tabla Markdown lista para pegar
en el documento de validación. Los casos de contenido (idioma, emojis,
sarcasmo) NO tienen una etiqueta "correcta" asumida: se registra lo que
responde el modelo para analizarlo en las conclusiones.
"""
import argparse
import json
import sys
import urllib.error
import urllib.request

# Algunas consolas de Windows usan cp1252 y no pueden imprimir emojis o ciertos
# caracteres Unicode de las entradas. Mantener UTF-8 evita que el reporte falle
# después de haber enviado las solicitudes a la API.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# (id, categoría, cuerpo JSON o texto, estado HTTP esperado o None si solo se observa)
LARGO = "The flight was great and the crew was kind. " * 40  # ~1,760 caracteres, >128 tokens
LIMITE = "x" * 5_000
EXCESO = "x" * 5_001

CASOS = [
    ("C01", "Inglés positivo", {"text": "The crew was helpful and kind."}, 200),
    ("C02", "Inglés negativo", {"text": "My luggage was lost and nobody helped me."}, 200),
    ("C03", "Inglés neutral", {"text": "The flight departs at 9:30 from gate 12."}, 200),
    ("C04", "Mixto", {"text": "The flight was delayed, but the crew was very helpful."}, 200),
    ("C05", "Español positivo", {"text": "El servicio fue excelente y el personal muy amable."}, 200),
    ("C06", "Español negativo", {"text": "Pésimo servicio, perdieron mi equipaje y nadie ayudó."}, 200),
    ("C07", "Español neutral", {"text": "El vuelo sale a las 9:30 de la puerta 12."}, 200),
    ("C08", "Sarcasmo", {"text": "Oh great, another two hour delay. Just what I needed."}, 200),
    ("C09", "Emojis positivos", {"text": "Amazing flight 😍✈️👏"}, 200),
    ("C10", "Emojis negativos", {"text": "Worst airline ever 😡👎"}, 200),
    ("C11", "Solo emojis", {"text": "😀😀😀"}, 200),
    ("C12", "Caracteres especiales", {"text": "<script>alert(1)</script> & \"quotes\" 'x' \\ % $"}, 200),
    ("C13", "Unicode no latino", {"text": "飞行很棒，机组人员很友好。"}, 200),
    ("C14", "Un solo carácter", {"text": "a"}, 200),
    ("C15", "Texto largo (>128 tokens)", {"text": LARGO}, 200),
    ("C16", "Límite exacto 5,000 caracteres", {"text": LIMITE}, 200),
    ("C17", "5,001 caracteres", {"text": EXCESO}, 422),
    ("C18", "Cadena vacía", {"text": ""}, 422),
    ("C19", "Solo espacios y saltos de línea", {"text": "   \n  "}, 422),
    ("C20", "Campo text ausente", {}, 422),
    ("C21", "text no es cadena", {"text": 123}, 422),
    ("C23", "Cuerpo de solicitud vacío", "", 422),
    ("C22", "JSON inválido", "{esto no es json", 422),
]


def enviar(api_url: str, cuerpo) -> tuple[int, dict]:
    """Envía un POST a /predict y devuelve (estado HTTP, JSON de respuesta)."""
    datos = cuerpo.encode() if isinstance(cuerpo, str) else json.dumps(cuerpo).encode()
    peticion = urllib.request.Request(
        f"{api_url.rstrip('/')}/predict",
        data=datos,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=120) as respuesta:
            return respuesta.status, json.load(respuesta)
    except urllib.error.HTTPError as error:
        try:
            return error.code, json.load(error)
        except ValueError:
            return error.code, {}


def resumir(texto: str, maximo: int = 40) -> str:
    """Acorta la entrada para la tabla y escapa el separador de columnas."""
    limpio = texto.replace("\n", "\\n").replace("|", "\\|")
    return limpio if len(limpio) <= maximo else f"{limpio[:maximo]}… ({len(texto)} car.)"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--salida", help="Archivo donde guardar la tabla Markdown")
    argumentos = parser.parse_args()

    try:
        urllib.request.urlopen(f"{argumentos.api_url.rstrip('/')}/health", timeout=10).read()
    except (urllib.error.URLError, OSError) as error:
        print(f"No se pudo conectar con {argumentos.api_url}: {error}", file=sys.stderr)
        print("Inicia la aplicación con `docker compose up --build` y espera a que el backend esté healthy.", file=sys.stderr)
        return 2

    filas = [
        "| ID | Categoría | Entrada | HTTP esperado | HTTP obtenido | Sentimiento | Etiqueta | Puntuación | Mensaje de error |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    desajustes = 0
    for id_caso, categoria, cuerpo, esperado in CASOS:
        estado, respuesta = enviar(argumentos.api_url, cuerpo)
        texto = cuerpo if isinstance(cuerpo, str) else str(cuerpo.get("text", "(sin campo)"))
        if estado != esperado:
            desajustes += 1
        puntuacion = f"{respuesta['score']:.1%}" if "score" in respuesta else "—"
        filas.append(
            f"| {id_caso} | {categoria} | {resumir(texto)} | {esperado} | {estado}"
            f"{'' if estado == esperado else ' ⚠'} | {respuesta.get('sentiment', '—')} | "
            f"{respuesta.get('original_label', '—')} | {puntuacion} | {resumir(respuesta.get('message', '—'), 120)} |"
        )

    tabla = "\n".join(filas)
    print(tabla)
    print(f"\nCasos: {len(CASOS)} · Estado HTTP distinto del esperado: {desajustes}")
    if argumentos.salida:
        with open(argumentos.salida, "w", encoding="utf-8") as archivo:
            archivo.write(tabla + "\n")
        print(f"Tabla guardada en {argumentos.salida}")
    return 0 if desajustes == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
