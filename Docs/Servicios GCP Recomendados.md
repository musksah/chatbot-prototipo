# Servicios GCP Recomendados para el Chatbot de Cootradecun

Este documento describe los servicios de Google Cloud Platform necesarios para desplegar el chatbot en producción, basado en los requerimientos del proyecto y el análisis del código actual.

---

## 1. Estado Actual del Código

| Componente | Implementación Actual | API Externa |
|------------|----------------------|-------------|
| **LLM** | `ChatGoogleGenerativeAI` (Gemini 3 Pro) | Google AI Studio |
| **Embeddings** | `OpenAIEmbeddings` (text-embedding-3-small) | OpenAI API |
| **Vector Store** | FAISS (en memoria) | Local |
| **API Backend** | FastAPI | Local |
| **Memoria de conversación** | `MemorySaver` (RAM) | Local |
| **Almacenamiento de docs** | PDFs en disco | Local |

> [!WARNING]
> El código actual usa **Google AI Studio** (API consumer) y **OpenAI** para embeddings. Para producción en GCP, se recomienda migrar a **Vertex AI** para consolidar servicios y reducir costos.

---

## 2. Servicios GCP Recomendados

### 2.1 Compute & Backend

| Servicio | Uso | Justificación |
|----------|-----|---------------|
| **Cloud Run** | Hosting de FastAPI | Serverless, escala a cero, pago por uso. Cumple SLA 99.9%. |
| **Cloud Functions** | Webhooks de WhatsApp, envío de OTP | Para tareas puntuales event-driven. |

### 2.2 Inteligencia Artificial

| Servicio | Uso | Migración desde |
|----------|-----|-----------------|
| **Vertex AI** (Gemini) | LLM para agentes conversacionales | `langchain-google-genai` → `langchain-google-vertexai` |
| **Vertex AI Embeddings** (Gecko) | Generación de embeddings para RAG | OpenAI Embeddings |
| **Vertex AI Vector Search** | Almacenamiento y búsqueda de vectores | FAISS en memoria |

### 2.3 Base de Datos & Almacenamiento

| Servicio | Uso | Justificación |
|----------|-----|---------------|
| **Cloud SQL (PostgreSQL)** | Usuarios, sesiones, logs de conversación, checkpoints de LangGraph | BD relacional gestionada con alta disponibilidad. |
| **Cloud Storage** | Almacenar PDFs (base de conocimiento RAG), certificados generados | Económico y escalable para archivos. |
| **Firestore** *(Alternativa)* | Estado de conversaciones, cache de sesiones | NoSQL para acceso rápido (opcional vs Cloud SQL). |

### 2.4 Seguridad

| Servicio | Uso |
|----------|-----|
| **Secret Manager** | API keys (Gemini, WhatsApp Business), credenciales de BD. |
| **Cloud Armor** | Protección DDoS y WAF para la API. |
| **Identity Platform** *(Opcional)* | Autenticación de usuarios del panel administrativo. |

### 2.5 Mensajería & Colas

| Servicio | Uso |
|----------|-----|
| **Cloud Pub/Sub** | Cola de mensajes para procesar WhatsApp de forma asíncrona. |
| **Cloud Tasks** | Programar envío de OTP, reintentos de mensajes fallidos. |

### 2.6 Monitoreo & Observabilidad

| Servicio | Uso |
|----------|-----|
| **Cloud Logging** | Logs centralizados de la aplicación. |
| **Cloud Monitoring** | Alertas de disponibilidad, latencia, errores. |
| **BigQuery** | Analítica de conversaciones, reportes de uso de tokens, intents. |
| **Looker Studio** | Dashboards para el módulo administrativo de reportes. |

### 2.7 CI/CD & DevOps

| Servicio | Uso |
|----------|-----|
| **Artifact Registry** | Almacenar imágenes Docker del backend. |
| **Cloud Build** | Pipeline CI/CD para automatizar despliegues. |

---

## 3. Arquitectura Propuesta

La solución se compone de **dos aplicaciones separadas**:

1. **Backend del Chatbot** - API que procesa mensajes de WhatsApp y ejecuta los agentes LLM.
2. **Dashboard Administrativo** - Aplicación web separada para monitoreo, reportes y gestión del RAG.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               ARQUITECTURA GENERAL                               │
└─────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────┐     ┌─────────────────────────────────┐
    │     BACKEND CHATBOT (App 1)     │     │   DASHBOARD ADMIN (App 2)       │
    └─────────────────────────────────┘     └─────────────────────────────────┘

┌───────────────────┐                        ┌───────────────────┐
│  WhatsApp Business│                        │   Usuarios Admin  │
│       API         │                        │   (Navegador)     │
└────────┬──────────┘                        └────────┬──────────┘
         │ Webhook                                    │ HTTPS
         ▼                                            ▼
┌─────────────────────────┐               ┌─────────────────────────┐
│      Cloud Run          │               │      Cloud Run          │
│  (FastAPI + LangGraph)  │               │  (Dashboard Frontend +  │
│    Langchain Agents     │               │   API de Reportes)      │
└────────┬────────────────┘               └────────┬────────────────┘
         │                                         │
         │         ┌───────────────────────────────┤
         │         │                               │
         ▼         ▼                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                        SERVICIOS COMPARTIDOS                      │
├──────────────────┬───────────────┬───────────────┬───────────────┤
│   Vertex AI      │ Cloud Storage │   Cloud SQL   │   BigQuery    │
│  (Gemini LLM +   │  (PDFs RAG)   │ (PostgreSQL)  │  (Analítica)  │
│   Embeddings)    │               │ - Checkpoints │ - Uso tokens  │
│                  │               │ - Sesiones    │ - Reportes    │
└──────────────────┴───────────────┴───────────────┴───────────────┘
```

> [!IMPORTANT]
> El **Dashboard Administrativo** es una aplicación independiente que consume datos de Cloud SQL y BigQuery para mostrar métricas de uso de tokens, conversaciones y gestión del RAG.

---

## 4. Mapeo de Requerimientos a Servicios

| Requerimiento (del documento de proyecto) | Servicios GCP |
|-------------------------------------------|---------------|
| Alta disponibilidad (99.9%) | Cloud Run + Cloud Monitoring + Load Balancing |
| RAG System para Q&A | Cloud Storage + Vertex AI Embeddings + Vector Search |
| Agentes LLM (conversación fluida) | Vertex AI (Gemini) |
| Autenticación OTP (SMS/Email) | Cloud Functions + Secret Manager |
| Módulo de Reportes y Monitoreo | BigQuery + Looker Studio + Cloud Logging |
| Escalabilidad (alto volumen concurrente) | Cloud Run (auto-scaling) + Cloud Pub/Sub |
| Seguridad de datos (cifrado) | Secret Manager + Cloud Armor + Cifrado nativo de GCP |
| Actualización de base de conocimiento RAG | Cloud Storage + Admin UI |

---

## 5. Cambios de Código Sugeridos (Para Migración)

### 5.1 Migrar LLM a Vertex AI

```python
# ANTES (agent.py)
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-3-pro-preview")

# DESPUÉS
from langchain_google_vertexai import ChatVertexAI
llm = ChatVertexAI(model_name="gemini-1.5-pro", project="PROJECT_ID", location="us-central1")
```

### 5.2 Migrar Embeddings a Vertex AI

```python
# ANTES (rag.py)
from langchain_openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# DESPUÉS
from langchain_google_vertexai import VertexAIEmbeddings
embeddings = VertexAIEmbeddings(model_name="textembedding-gecko@003", project="PROJECT_ID")
```

### 5.3 Nueva Dependencia

```txt
# requirements.txt - agregar:
langchain-google-vertexai
google-cloud-aiplatform
```

---

## 6. Estimación de Costos (Referencia)

| Servicio | Tier/SKU | Costo Estimado (USD/mes) |
|----------|----------|--------------------------|
| Cloud Run | 1 vCPU, 512MB RAM, ~100K requests | ~$10-30 |
| Vertex AI (Gemini 1.5 Pro) | ~500K tokens input, ~100K output | ~$20-50 |
| Vertex AI Embeddings | ~1M tokens | ~$0.10 |
| Cloud SQL (PostgreSQL) | db-f1-micro, 10GB | ~$10-15 |
| Cloud Storage | 1GB Standard | ~$0.02 |
| Secret Manager | 6 secretos, 10K accesos | ~$0.50 |
| **Total estimado MVP** | | **~$50-100/mes** |

> [!NOTE]
> Los costos varían según el uso. Se recomienda configurar **Cloud Billing Alerts** para monitorear gastos.

---

## 7. Próximos Pasos

1. [ ] Crear proyecto en GCP y habilitar APIs (Vertex AI, Cloud Run, Cloud SQL).
2. [ ] Configurar cuenta de servicio con permisos necesarios.
3. [ ] Migrar código para usar `langchain-google-vertexai`.
4. [ ] Crear bucket en Cloud Storage para documentos RAG.
5. [ ] Configurar Cloud SQL para persistencia de checkpoints.
6. [ ] Desplegar primera versión en Cloud Run.
7. [ ] Configurar webhook de WhatsApp Business API.
