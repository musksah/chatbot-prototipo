# 🤖 Chatbot COOTRADECUN

Chatbot inteligente para la Cooperativa Multiactiva de Trabajadores de la Educación (COOTRADECUN), basado en agentes LLM y sistema RAG.

## 📋 Requisitos Previos

- **Python 3.10+**
- **Node.js 18+** (para el frontend)
- **Google Cloud SDK** (opcional, para GCS y despliegue)

---

## 🚀 Despliegue Local

### Backend (FastAPI + LangGraph)

1. **Navegar al directorio del backend:**
   ```bash
   cd backend
   ```

2. **Crear entorno virtual (si no existe):**
   ```bash
   python -m venv venv
   ```

3. **Activar el entorno virtual:**

   **Windows (PowerShell):**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

   **Windows (CMD):**
   ```cmd
   .\venv\Scripts\activate.bat
   ```

   **Linux/macOS:**
   ```bash
   source venv/bin/activate
   ```

4. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configurar variables de entorno:**
   
   Copia el archivo `.env.example` a `.env` y configura las variables:
   ```bash
   cp .env.example .env
   ```

   Variables requeridas:
   ```env
   # LLM API Keys
   GOOGLE_API_KEY=tu_api_key_de_gemini
   
   # Twilio (para OTP)
   TWILIO_ACCOUNT_SID=tu_account_sid
   TWILIO_AUTH_TOKEN=tu_auth_token
   TWILIO_VERIFY_SERVICE_SID=tu_verify_service_sid
   
   # GCS (opcional, para certificados PDF)
   GCP_PROJECT_ID=tu_proyecto_gcp
   GCS_BUCKET_NAME=nombre_del_bucket
   ```

6. **Ejecutar el servidor:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   El backend estará disponible en: `http://localhost:8000`

---

### Frontend (React + Vite)

1. **Navegar al directorio del frontend:**
   ```bash
   cd frontend-react
   ```

2. **Instalar dependencias:**
   ```bash
   npm install
   ```

3. **Configurar la URL del backend (opcional):**
   
   Para desarrollo local, el frontend apunta a `http://localhost:8000` por defecto.
   
   Para producción, crea un archivo `.env.production`:
   ```env
   VITE_API_URL=https://tu-backend-url.run.app
   ```

4. **Ejecutar el servidor de desarrollo:**
   ```bash
   npm run dev
   ```

   El frontend estará disponible en: `http://localhost:5173`

---

## 📁 Estructura del Proyecto

```
chatbot-prototipo/
├── backend/
│   ├── app/
│   │   ├── main.py           # API FastAPI
│   │   ├── agent.py          # Agentes LangGraph
│   │   ├── tools.py          # Herramientas de los agentes
│   │   ├── rag.py            # Sistema RAG con FAISS
│   │   ├── otp.py            # Autenticación OTP (Twilio)
│   │   ├── pdf_generator.py  # Generación de PDFs
│   │   └── gcs_storage.py    # Integración con GCS
│   ├── docs/                  # PDFs de base de conocimiento
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
│
├── frontend-react/
│   ├── src/
│   │   ├── App.jsx           # Componente principal
│   │   ├── Login.jsx         # Pantalla de login
│   │   └── ...
│   ├── package.json
│   └── Dockerfile
│
├── Docs/                      # Documentación del proyecto
├── DEPLOY_CLOUD_RUN.md       # Guía de despliegue a GCP
└── TESTING_GUIDE.md          # Guía de pruebas
```

---

## 🔧 Características

### Agentes Especializados
- **Primary Assistant**: Router principal y preguntas generales
- **Atención al Asociado**: Requisitos, auxilios, convenios
- **Nóminas**: Pagos, desprendibles, deducciones
- **Vivienda**: Proyectos de vivienda, créditos
- **Certificados**: Generación de certificados con autenticación OTP

### Sistema RAG
- Indexación de documentos PDF (vivienda, nóminas, atención al asociado)
- Búsqueda semántica con FAISS y embeddings de Google

### Generación de Certificados PDF
- Certificados tributarios en formato PDF profesional
- Almacenamiento en Google Cloud Storage (producción)
- URLs firmadas con expiración de 24 horas

### Autenticación OTP
- Verificación por SMS/WhatsApp vía Twilio
- Requerido para la generación de certificados

---

## 🌐 Despliegue en Producción (Cloud Run)

Consulta la guía completa en [DEPLOY_CLOUD_RUN.md](./DEPLOY_CLOUD_RUN.md)

**Resumen rápido:**
```bash
# Backend
cd backend
gcloud builds submit --tag us-central1-docker.pkg.dev/PROJECT_ID/chatbot-repo/chatbot-backend
gcloud run deploy chatbot-backend --image ... --allow-unauthenticated

# Frontend
cd frontend-react
gcloud builds submit --tag us-central1-docker.pkg.dev/PROJECT_ID/chatbot-repo/chatbot-frontend
gcloud run deploy chatbot-frontend --image ... --allow-unauthenticated
```

---

## 📖 Documentación Adicional

- [Definición del Proyecto](./Docs/Definición%20del%20Proyecto%20ChatBot.md)
- [Servicios GCP Recomendados](./Docs/Servicios%20GCP%20Recomendados.md)
- [Guía de Pruebas](./TESTING_GUIDE.md)
- [Despliegue en Cloud Run](./DEPLOY_CLOUD_RUN.md)

---

## 🛠️ Comandos Útiles

```bash
# Activar venv (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Instalar nueva dependencia en el venv
.\venv\Scripts\pip install nombre_paquete

# Ver logs del backend
uvicorn app.main:app --reload --log-level debug

# Construir frontend para producción
cd frontend-react && npm run build
```

---

## 📝 Licencia

Proyecto privado de COOTRADECUN.
