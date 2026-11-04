# Resultados de pruebas extremas de la API

- Fecha de ejecuci?n: 2026-11-03.
- Destino: API FastAPI real en Docker, `http://127.0.0.1:8000`.
- Entorno: Docker Engine 29.9.2; backend `healthy`, frontend activo; `GET /health` devolvi? `{"status":"ok","model_loaded":true}`.
- Resultado de contrato HTTP: 23 casos ejecutados; los 23 c?digos obtenidos coincidieron con los esperados; 0 discrepancias.
- La suite automatizada local ejecutada el mismo d?a obtuvo 13 aprobadas y 1 warning de deprecaci?n de Starlette/AnyIO.
- Las etiquetas, sentimientos y puntuaciones son salidas observadas del modelo, no una comparaci?n con etiquetas verdaderas. Estas pruebas no miden precisi?n ni exactitud.

## Resultados por caso

| ID | Categoría | Entrada | HTTP esperado | HTTP obtenido | Sentimiento | Etiqueta | Puntuación | Mensaje de error |
|---|---|---|---|---|---|---|---|---|
| C01 | Inglés positivo | The crew was helpful and kind. | 200 | 200 | Positivo | POS | 98.8% | — |
| C02 | Inglés negativo | My luggage was lost and nobody helped me… (41 car.) | 200 | 200 | Negativo | NEG | 97.3% | — |
| C03 | Inglés neutral | The flight departs at 9:30 from gate 12. | 200 | 200 | Neutral | NEU | 96.6% | — |
| C04 | Mixto | The flight was delayed, but the crew was… (54 car.) | 200 | 200 | Positivo | POS | 85.8% | — |
| C05 | Español positivo | El servicio fue excelente y el personal … (51 car.) | 200 | 200 | Positivo | POS | 98.2% | — |
| C06 | Español negativo | Pésimo servicio, perdieron mi equipaje y… (53 car.) | 200 | 200 | Neutral | NEU | 95.7% | — |
| C07 | Español neutral | El vuelo sale a las 9:30 de la puerta 12… (41 car.) | 200 | 200 | Neutral | NEU | 97.3% | — |
| C08 | Sarcasmo | Oh great, another two hour delay. Just w… (53 car.) | 200 | 200 | Negativo | NEG | 96.9% | — |
| C09 | Emojis positivos | Amazing flight 😍✈️👏 | 200 | 200 | Positivo | POS | 98.9% | — |
| C10 | Emojis negativos | Worst airline ever 😡👎 | 200 | 200 | Negativo | NEG | 98.2% | — |
| C11 | Solo emojis | 😀😀😀 | 200 | 200 | Neutral | NEU | 90.1% | — |
| C12 | Caracteres especiales | <script>alert(1)</script> & "quotes" 'x'… (46 car.) | 200 | 200 | Neutral | NEU | 96.2% | — |
| C13 | Unicode no latino | 飞行很棒，机组人员很友好。 | 200 | 200 | Neutral | NEU | 93.4% | — |
| C14 | Un solo carácter | a | 200 | 200 | Neutral | NEU | 86.6% | — |
| C15 | Texto largo (>128 tokens) | The flight was great and the crew was ki… (1760 car.) | 200 | 200 | Positivo | POS | 98.8% | — |
| C16 | Límite exacto 5,000 caracteres | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx… (5000 car.) | 200 | 200 | Neutral | NEU | 93.1% | — |
| C17 | 5,001 caracteres | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx… (5001 car.) | 422 | 422 | — | — | — | El texto supera el máximo permitido de 5000 caracteres. |
| C18 | Cadena vacía |  | 422 | 422 | — | — | — | El texto no puede estar vacío ni contener solo espacios. |
| C19 | Solo espacios y saltos de línea |    \n   | 422 | 422 | — | — | — | El texto no puede estar vacío ni contener solo espacios. |
| C20 | Campo text ausente | (sin campo) | 422 | 422 | — | — | — | La solicitud debe incluir el campo 'text'. |
| C21 | text no es cadena | 123 | 422 | 422 | — | — | — | Solicitud inválida. Envía un JSON con el campo 'text' como texto. |
| C23 | Cuerpo de solicitud vacío |  | 422 | 422 | — | — | — | La solicitud debe incluir el campo 'text'. |
| C22 | JSON inválido | {esto no es json | 422 | 422 | — | — | — | Solicitud inválida. Envía un JSON con el campo 'text' como texto. |

## Metodolog?a

Se confirm? la configuraci?n con `docker compose config --quiet`, el estado de servicios con `docker compose ps` y la disponibilidad del modelo mediante `GET /health`. Despu?s se ejecut? `scripts/pruebas_extremas.py --api-url http://127.0.0.1:8000 --salida resultados_pruebas_extremas_2026-11-03.md`. El script envi? las 23 peticiones HTTP directamente al backend Docker activo; no utiliz? mocks para esta bater?a. C23 se envi? con cuerpo HTTP de cero bytes y recibi? 422. La tabla completa registra los c?digos reales y cualquier salida JSON presente.

## An?lisis de observaciones

- C06, comentario negativo en espa?ol, recibi? `Neutral` / `NEU` con 95.7 %. Es una observaci?n sem?nticamente inesperada que puede relacionarse con idioma o dominio; no es un error del endpoint. No hay verdad de referencia para atribuir causa ni calcular exactitud.
- C11, emojis positivos aislados, recibi? `Neutral` / `NEU` con 90.1 %. Se registra como limitaci?n observada de esa entrada, no como fallo HTTP.
- C08 (sarcasmo) fue clasificado `Negativo` / `NEG` con 96.9 %; un solo ejemplo no permite concluir capacidad general para detectar sarcasmo.
- C15 (1,760 caracteres, descrito como superior a 128 tokens) y C16 (5,000 caracteres) recibieron HTTP 200. El proyecto configura truncamiento a 128 tokens; la bater?a no inspecciona directamente la secuencia tokenizada ni demuestra que todo el contenido largo influya en la salida.
- C17 (5,001 caracteres), C18 (vac?o), C19 (solo espacios), C20 (campo ausente), C21 (tipo incorrecto), C22 (JSON mal formado) y C23 (cuerpo vac?o) recibieron HTTP 422 seg?n lo esperado.
- Las puntuaciones softmax mostradas no son confianza calibrada. No se compararon predicciones con etiquetas de referencia; por tanto, no se midieron precisi?n, exactitud ni generalizaci?n.

## Incidencia del script y correcci?n

La primera ejecuci?n real complet? las solicitudes, pero la consola Windows con codificaci?n cp1252 no pudo imprimir algunos caracteres Unicode y el proceso termin? antes de guardar la tabla. Se ajust? `scripts/pruebas_extremas.py` para usar salida UTF-8 cuando la consola permite reconfigurarla y se repiti? la bater?a completa. El archivo de esta ejecuci?n se guard? como `resultados_pruebas_extremas_2026-11-03.md`.
