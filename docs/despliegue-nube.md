# Manual futuro de despliegue en Azure Container Apps

> Este procedimiento es una propuesta reproducible. No se han ejecutado comandos de Azure, no se han creado recursos cloud y no se ha desplegado la aplicación.

## Arquitectura

El navegador se conecta por HTTPS al frontend Streamlit (ingress externo, puerto 8501). Streamlit llama a FastAPI por HTTP dentro del mismo Azure Container Apps Environment, usando el FQDN interno. FastAPI usa ingress interno (puerto 8000) y no se publica directamente en Internet. El backend descarga el checkpoint público de Hugging Face en su primer inicio. El flujo interno en HTTP es el recomendado para el app name/FQDN interno de Container Apps; HTTPS se termina en el ingress público del frontend. Microsoft indica que las llamadas entre apps del mismo entorno permanecen dentro de ese entorno y documenta el uso de `http://<APP_NAME>` para llamadas internas ([comunicación entre apps](https://learn.microsoft.com/en-us/azure/container-apps/connect-apps), [ingress](https://learn.microsoft.com/en-us/azure/container-apps/ingress)).

## Requisitos

- Suscripción Azure activa, Azure CLI actualizado y permisos para crear grupo de recursos, ACR, identidad administrada y Container Apps.
- Dockerfiles existentes en `backend/Dockerfile` y `frontend/Dockerfile`; ejecutar desde la raíz del repositorio.
- Región con cuotas disponibles para Azure Container Apps y Azure Container Registry.
- Dimensionamiento inicial por validar: backend 2 vCPU / 4 GiB; frontend 0.5 vCPU / 1 GiB. Medir consumo y latencia antes de uso real.
- Considerar costos de cómputo, ACR, logs, transferencia y almacenamiento persistente de la caché.

## Procedimiento propuesto en PowerShell

Los comandos siguientes son una guía futura. Sustituye los valores de ejemplo y revisa cuotas y costos antes de ejecutar.

### 1. Preparar Azure CLI y recursos base

```powershell
az login
az account set --subscription "<SUBSCRIPTION_ID>"
az extension add --name containerapp --upgrade
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights

$RG = "rg-fase2-sentimientos"
$LOCATION = "eastus"
$ACR = "acrfase2<cadenaunica>"
$ENV = "aca-fase2-sentimientos"
$IDENTITY = "id-fase2-containerapps"
$API = "api-bertweet"
$WEB = "web-bertweet"

az group create --name $RG --location $LOCATION
```

El nombre de ACR debe ser globalmente único, en minúsculas y alfanumérico.

### 2. Crear ACR privado y construir las imágenes

```powershell
az acr create --name $ACR --resource-group $RG --location $LOCATION --sku Basic --admin-enabled false
az acr config authentication-as-arm update --registry $ACR --status enabled

az acr build --registry $ACR --image bertweet-backend:1.0 --file backend/Dockerfile .
az acr build --registry $ACR --image sentiment-frontend:1.0 --file frontend/Dockerfile .
```

El punto final es el contexto de construcción en la raíz del repositorio. Usa tags inmutables o versionados; evita reemplazar imágenes ya desplegadas. La construcción remota con `az acr build` está documentada por Microsoft ([tutorial ACR](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-tutorial-quick-task)).

### 3. Asignar identidad administrada para descargar imágenes

```powershell
$identityInfo = az identity create --name $IDENTITY --resource-group $RG --location $LOCATION | ConvertFrom-Json
$IDENTITY_ID = $identityInfo.id
$PRINCIPAL_ID = $identityInfo.principalId
$ACR_ID = az acr show --name $ACR --resource-group $RG --query id --output tsv

az role assignment create --assignee-object-id $PRINCIPAL_ID --assignee-principal-type ServicePrincipal --role AcrPull --scope $ACR_ID
```

La identidad necesita el rol `AcrPull` y se asignará a ambas aplicaciones para extraer imágenes; no se habilitan credenciales de administrador. Considera el tiempo de propagación del rol. La configuración con identidad administrada se describe en [Microsoft Learn](https://learn.microsoft.com/en-us/azure/container-apps/managed-identity-image-pull).

### 4. Crear el entorno de Container Apps

```powershell
az containerapp env create --name $ENV --resource-group $RG --location $LOCATION
az containerapp env show --name $ENV --resource-group $RG --query properties.provisioningState --output tsv
```

Continúa cuando el estado sea `Succeeded`. El Environment proporciona el límite de red y resolución de nombres entre aplicaciones.

### 5. Desplegar FastAPI con ingreso privado

```powershell
$REGISTRY = "$ACR.azurecr.io"
az containerapp create --name $API --resource-group $RG --environment $ENV --image "$REGISTRY/bertweet-backend:1.0" --ingress internal --target-port 8000 --registry-server $REGISTRY --registry-identity $IDENTITY_ID --user-assigned $IDENTITY_ID --env-vars HF_HOME=/home/app/.cache/huggingface --cpu 2.0 --memory 4.0Gi --min-replicas 1 --max-replicas 1

$API_FQDN = az containerapp show --name $API --resource-group $RG --query properties.configuration.ingress.fqdn --output tsv
$API_URL = "http://" + $API_FQDN
az containerapp show --name $API --resource-group $RG --query properties.configuration.ingress.external --output tsv
```

Confirma que `external` sea `false` y que el FQDN interno corresponda al mismo Environment. Conserva `API_URL` solo como variable del frontend.

### 6. Desplegar Streamlit como único servicio público

```powershell
az containerapp create --name $WEB --resource-group $RG --environment $ENV --image "$REGISTRY/sentiment-frontend:1.0" --ingress external --target-port 8501 --allow-insecure false --registry-server $REGISTRY --registry-identity $IDENTITY_ID --user-assigned $IDENTITY_ID --env-vars "API_URL=$API_URL" --cpu 0.5 --memory 1.0Gi --min-replicas 1 --max-replicas 2

$WEB_FQDN = az containerapp show --name $WEB --resource-group $RG --query properties.configuration.ingress.fqdn --output tsv
"https://$WEB_FQDN"
```

Con `allow-insecure false`, el ingress público redirige HTTP a HTTPS. Solo el frontend tiene `external` habilitado; la API permanece privada.

### 7. Validar una futura implementación

```powershell
az containerapp show --name $API --resource-group $RG --query properties.configuration.ingress --output json
az containerapp show --name $WEB --resource-group $RG --query properties.configuration.ingress --output json
az containerapp logs show --name $API --resource-group $RG --type console --tail 50
az containerapp logs show --name $WEB --resource-group $RG --type console --tail 50
Invoke-WebRequest -Uri "https://$WEB_FQDN"
```

Comprueba que FastAPI esté en ingreso interno, Streamlit en ingreso externo con el puerto 8501 y HTTP inseguro deshabilitado. Revisa los logs de carga del modelo y ejecuta `/health` y una predicción desde la UI. No abras el FQDN interno de FastAPI desde Internet. Guarda únicamente capturas y logs obtenidos en la ejecución futura, indicando fecha y entorno.

## Variables, seguridad y mantenimiento

- `API_URL`: FQDN privado de FastAPI, con `http://` interno.
- `HF_HOME`: `/home/app/.cache/huggingface`; define ubicación de caché en el backend.
- El modelo es público; no se necesita `HF_TOKEN`. Si esto cambia, usa Key Vault o secretos administrados; nunca Git, Dockerfile ni logs.
- No publiques FastAPI ni el almacenamiento de caché. Restringe quién puede utilizar el frontend; el sitio público sin autenticación permite a visitantes solicitar inferencias.
- Aplica mínimo privilegio, usa identidad administrada para ACR, fija tags de imagen, actualiza dependencias y supervisa CPU, memoria, reinicios, latencia y errores.
- Decide si se requiere Azure Files para conservar pesos entre revisiones. La caché local de Docker no se traslada a Azure; almacenamiento compartido agrega costos y requiere validar permisos y concurrencia.
- Define procedimiento de rollback a un tag de imagen anterior y una política de retención de logs que evite almacenar comentarios personales innecesariamente.

## Costos, limitaciones y estado

Evalúa precios por región de CPU/memoria, réplicas, ACR, Azure Files si se usa, Log Analytics, transferencia, dominio y controles perimetrales. No se incluyen importes porque dependen de región y uso; consulta la [calculadora de Azure](https://azure.microsoft.com/pricing/calculator/).

BERTweet fue preparado para publicaciones de Twitter en inglés. Las salidas de los casos puntuales no demuestran calidad en español o comentarios de aerolíneas. Antes de uso real hace falta una evaluación representativa etiquetada y revisión de privacidad/licencia.

**Estado:** este manual describe únicamente un procedimiento futuro. No se ejecutaron comandos de Azure ni se realizó un despliegue.
