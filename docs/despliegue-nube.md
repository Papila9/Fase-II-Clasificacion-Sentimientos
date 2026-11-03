# Manual futuro de despliegue en la nube

> Este documento describe una estrategia futura. No se ha realizado ningún despliegue.

## Requerimientos técnicos

- Cuenta en un proveedor de nube con registro de imágenes y servicio de contenedores.
- Docker y Docker Compose v2.33.1 o posterior para validar localmente la misma configuración.
- Imagen backend con Python 3.11, FastAPI, PyTorch y Transformers; imagen frontend con Streamlit.
- Almacenamiento persistente para la caché del modelo o una política clara de descarga al iniciar.
- Memoria suficiente para cargar BERTweet. Medir consumo real antes de seleccionar el tamaño de instancia.
- HTTPS, dominio y certificado TLS para cualquier acceso público.
- Revisar las condiciones de licencia: la ficha del modelo limita su uso a investigación científica y fines no comerciales.

## Arquitectura propuesta

El navegador se conectaría al frontend Streamlit publicado. El frontend llamaría al servicio FastAPI mediante una red privada del proveedor. El backend descargaría el modelo público de Hugging Face en el primer inicio y podría conservar la caché en almacenamiento persistente. Solo el frontend estaría expuesto a Internet; la API quedaría privada salvo que se defina autenticación y una necesidad justificada.

## Estrategia basada en contenedores

1. Ejecutar pruebas automatizadas y revisión de seguridad local.
2. Construir imágenes reproducibles del backend y frontend usando versiones fijadas.
3. Etiquetarlas con versión inmutable y publicarlas en un registro privado.
4. Crear los servicios en una red privada, con frontend expuesto mediante HTTPS y API accesible solo desde el frontend.
5. Configurar almacenamiento/cache persistente para reducir descargas repetidas del modelo.
6. Probar health checks, logs, reinicio, latencia y límites de recursos en un entorno de prueba.
7. Promover la misma versión de imagen a producción y documentar rollback.

## Configuración y variables

Las variables actuales de Compose (`FRONTEND_PORT`, `BACKEND_PORT`) solo controlan puertos locales. En nube, usar la configuración del proveedor para puertos, URL privada de API, tamaño máximo de texto, logging y ubicación de caché. Si en el futuro se requiere `HF_TOKEN` (el modelo revisado es público), almacenarlo en un gestor de secretos y nunca en Git, imagen o logs. No se han agregado tokens a este proyecto.

## Seguridad

- Publicar únicamente el frontend; mantener API y red del modelo privadas.
- Usar HTTPS, limitar orígenes/redes, proteger administración y aplicar mínimo privilegio.
- Escanear dependencias e imágenes, actualizar parches y fijar versiones y digest de imágenes.
- Definir límites de solicitudes, tamaño de texto, concurrencia y tiempos de espera.
- No registrar texto personal sin una necesidad, consentimiento y política de retención.
- Evitar secretos en Dockerfile, repositorio, variables visibles al cliente o logs.

## Mantenimiento y monitoreo

Revisar logs y health checks, medir latencia/errores/memoria, actualizar imágenes de forma controlada, validar el identificador y licencia del modelo y conservar una estrategia de rollback. La caché debe tener permisos restringidos y espacio supervisado.

## Costos y limitaciones por evaluar

Cotizar cómputo, memoria, almacenamiento de caché, transferencia, registro de imágenes, balanceador, dominio/TLS y monitoreo. La inferencia CPU puede tener latencia relevante y la descarga inicial consume red y disco; GPU eleva costos. BERTweet fue preentrenado para inglés de Twitter y su calidad en comentarios de aerolíneas o español no está garantizada por esta aplicación. Antes de uso real se requiere evaluación representativa y revisión de privacidad.
