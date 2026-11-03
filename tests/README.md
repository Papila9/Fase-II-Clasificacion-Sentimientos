# Pruebas

Desde la raíz del proyecto, instala `requirements-dev.txt` y ejecuta `python -m pytest -q`. Las pruebas inyectan un analizador simulado para no descargar el modelo. La validación real requiere además iniciar el backend con el checkpoint.
