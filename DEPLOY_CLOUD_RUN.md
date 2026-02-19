# Guía de Despliegue en Google Cloud Run

Esta guía explica cómo desplegar el chatbot (backend y frontend) en Google Cloud Run.

## Prerrequisitos

1. **Google Cloud SDK** instalado: https://cloud.google.com/sdk/docs/install
2. **Docker** instalado (opcional si usas Cloud Build)
3. **Proyecto GCP** creado con billing habilitado

## Configuración Inicial

```bash
# Autenticarse en GCP
gcloud auth login

# Configurar proyecto
gcloud config set project corvus-data-testing

# Habilitar APIs necesarias
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

---

## 1. Desplegar Backend

### 1.1 Crear repositorio en Artifact Registry

```bash
gcloud artifacts repositories create chatbot-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="Repositorio del Chatbot"
```

### 1.2 Construir y subir imagen del Backend

```bash
cd backend

# Construir con Cloud Build
gcloud builds submit --tag us-central1-docker.pkg.dev/corvus-data-testing/chatbot-repo/chatbot-backend

# O construir localmente y subir
docker build -t us-central1-docker.pkg.dev/corvus-data-testing/chatbot-repo/chatbot-backend .
docker push us-central1-docker.pkg.dev/corvus-data-testing/chatbot-repo/chatbot-backend
```

### 1.3 Desplegar en Cloud Run

```bash
gcloud run deploy chatbot-backend \
    --image us-central1-docker.pkg.dev/corvus-data-testing/chatbot-repo/chatbot-backend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "GOOGLE_API_KEY=tu_api_key,OPENAI_API_KEY=tu_openai_key"
```

> **Nota:** Anota la URL del backend (ej: `https://chatbot-backend-xxxxx.run.app`)

---

## 2. Desplegar Frontend

### 2.1 Configurar URL del Backend

Crea un archivo `.env.production` en `frontend-react/`:

```bash
VITE_API_URL=https://chatbot-backend-xxxxx.run.app
```

### 2.2 Construir y subir imagen del Frontend

```bash
cd frontend-react

# Construir con Cloud Build
gcloud builds submit --tag us-central1-docker.pkg.dev/corvus-data-testing/chatbot-repo/chatbot-frontend

# O construir localmente
docker build -t us-central1-docker.pkg.dev/corvus-data-testing/chatbot-repo/chatbot-frontend .
docker push us-central1-docker.pkg.dev/corvus-data-testing/chatbot-repo/chatbot-frontend
```

### 2.3 Desplegar en Cloud Run

```bash
gcloud run deploy chatbot-frontend \
    --image us-central1-docker.pkg.dev/corvus-data-testing/chatbot-repo/chatbot-frontend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated
```

---

## 3. Configurar CORS en Backend

Actualiza `backend/app/main.py` para permitir el dominio del frontend:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://chatbot-frontend-xxxxx.run.app",  # Agregar URL de Cloud Run
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 4. URLs Finales

| Servicio | URL |
|----------|-----|
| **Frontend** | `https://chatbot-frontend-xxxxx.run.app` |
| **Backend** | `https://chatbot-backend-xxxxx.run.app` |

---

## 5. Comandos Útiles

```bash
# Ver logs
gcloud run logs read --service chatbot-backend --region us-central1

# Actualizar servicio
gcloud run services update chatbot-backend --region us-central1 --set-env-vars "VAR=value"

# Ver servicios desplegados
gcloud run services list --region us-central1
```

---

## Costos Estimados

| Servicio | Costo Aprox. |
|----------|--------------|
| Cloud Run (2 servicios) | ~$10-30/mes |
| Artifact Registry | ~$0.10/GB |
| **Total MVP** | **~$15-40/mes** |
