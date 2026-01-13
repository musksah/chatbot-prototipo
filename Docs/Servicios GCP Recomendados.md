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

## 2. Modelo de Arquitectura: Cliente vs Plataforma

La solución se divide en **dos ambientes GCP separados**:

| Ambiente | Descripción | Propietario |
|----------|-------------|-------------|
| **Proyecto Cliente** | Backend del chatbot y recursos dedicados por cliente | El cliente (ej: Cootradecun) |
| **Proyecto Plataforma** | Dashboard Administrativo multi-tenant (White-Label) | Proveedor (licencia mensual) |

> [!IMPORTANT]
> El **Dashboard Administrativo** es una aplicación **SaaS multi-tenant** que se licencia mensualmente a los clientes. No es propiedad del cliente, sino que se le da acceso mediante licencia.

---

## 3. Recursos GCP del Cliente (Chatbot)

Estos recursos son desplegados en el **proyecto GCP del cliente** y son de su propiedad.

### 3.1 Compute

| Servicio | Uso |
|----------|-----|
| **Cloud Run** | Backend del Chatbot (FastAPI + LangGraph + Agentes) |

### 3.2 Inteligencia Artificial

| Servicio | Uso |
|----------|-----|
| **Vertex AI (Gemini)** | LLM para agentes conversacionales |
| **Vertex AI Embeddings** | Generación de embeddings para RAG |
| **Vertex AI Vector Search** | Búsqueda semántica de documentos |

### 3.3 Base de Datos & Almacenamiento

| Servicio | Uso |
|----------|-----|
| **Cloud SQL (PostgreSQL)** | Checkpoints de LangGraph, sesiones de usuario, logs |
| **Cloud Storage** | PDFs de base de conocimiento, certificados generados |

### 3.4 Seguridad & Mensajería

| Servicio | Uso |
|----------|-----|
| **Secret Manager** | API keys (Gemini, WhatsApp Business, Twilio) |
| **Cloud Tasks** | Procesamiento asíncrono de WhatsApp, envío de OTP |
| **Cloud Armor** | Protección DDoS y WAF |

### 3.5 Monitoreo

| Servicio | Uso |
|----------|-----|
| **Cloud Logging** | Logs centralizados |
| **Cloud Monitoring** | Alertas de disponibilidad y errores |

---

## 4. Recursos GCP de la Plataforma (Dashboard Admin - White-Label)

Estos recursos son desplegados en el **proyecto GCP del proveedor** y son multi-tenant.

### 4.1 Compute

| Servicio | Uso |
|----------|-----|
| **Cloud Run** | Dashboard Frontend + API de Reportes (multi-tenant) |

### 4.2 Base de Datos

| Servicio | Uso |
|----------|-----|
| **Cloud SQL (PostgreSQL)** | Datos de usuarios admin, configuración de tenants, licencias |

### 4.3 Seguridad

| Servicio | Uso |
|----------|-----|
| **Identity Platform** | Autenticación de usuarios del dashboard |
| **Secret Manager** | Credenciales de conexión a proyectos de clientes |

### 4.4 CI/CD

| Servicio | Uso |
|----------|-----|
| **Artifact Registry** | Imágenes Docker del dashboard |
| **Cloud Build** | Pipeline CI/CD |

---

## 5. Arquitectura Multi-Tenant

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          PROYECTO PROVEEDOR (SaaS)                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │            DASHBOARD ADMIN (White-Label Multi-Tenant)                     │   │
│  │                        Cloud Run                                          │   │
│  └─────────────────────────────┬────────────────────────────────────────────┘   │
│                                │                                                 │
│              ┌─────────────────┼─────────────────┐                              │
│              │                 │                 │                              │
│              ▼                 ▼                 ▼                              │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐                   │
│  │ Cloud SQL        │  │ Identity     │  │ Secret Manager   │                   │
│  │ (Tenants/Users)  │  │ Platform     │  │ (Client Keys)    │                   │
│  └──────────────────┘  └──────────────┘  └──────────────────┘                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
              │                   │                    │
              │    Conexión API   │                    │
              ▼                   ▼                    ▼
┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐
│  PROYECTO CLIENTE A     │  │  PROYECTO CLIENTE B     │  │  PROYECTO CLIENTE C     │
│  (Cootradecun)          │  │  (Cliente 2)            │  │  (Cliente 3)            │
├─────────────────────────┤  ├─────────────────────────┤  ├─────────────────────────┤
│ ┌─────────────────────┐ │  │ ┌─────────────────────┐ │  │ ┌─────────────────────┐ │
│ │   Cloud Run         │ │  │ │   Cloud Run         │ │  │ │   Cloud Run         │ │
│ │   (Backend)         │ │  │ │   (Backend)         │ │  │ │   (Backend)         │ │
│ └─────────────────────┘ │  │ └─────────────────────┘ │  │ └─────────────────────┘ │
│ ┌─────────────────────┐ │  │ ┌─────────────────────┐ │  │ ┌─────────────────────┐ │
│ │ Vertex AI + SQL     │ │  │ │ Vertex AI + SQL     │ │  │ │ Vertex AI + SQL     │ │
│ │ Storage + Tasks     │ │  │ │ Storage + Tasks     │ │  │ │ Storage + Tasks     │ │
│ └─────────────────────┘ │  │ └─────────────────────┘ │  │ └─────────────────────┘ │
└─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘
```

> [!NOTE]
> El Dashboard se conecta a los proyectos de clientes mediante **Service Account Keys** almacenadas en Secret Manager del proveedor.

---

## 6. Mapeo de Requerimientos a Servicios

| Requerimiento (del documento de proyecto) | Servicios GCP |
|-------------------------------------------|---------------|
| Alta disponibilidad (99.9%) | Cloud Run + Cloud Monitoring + Load Balancing |
| RAG System para Q&A | Cloud Storage + Vertex AI Embeddings + Vector Search |
| Agentes LLM (conversación fluida) | Vertex AI (Gemini) |
| Autenticación OTP (SMS/Email) | Cloud Functions + Secret Manager |
| Módulo de Reportes y Monitoreo | Cloud SQL + Cloud Logging |
| Escalabilidad (alto volumen concurrente) | Cloud Run (auto-scaling) + Cloud Tasks |
| Seguridad de datos (cifrado) | Secret Manager + Cloud Armor + Cifrado nativo de GCP |
| Actualización de base de conocimiento RAG | Cloud Storage + Admin UI |

---

## 7. Estimación de Costos por Cliente (Referencia)

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

## 8. Próximos Pasos

1. [ ] Crear proyecto en GCP y habilitar APIs (Vertex AI, Cloud Run, Cloud SQL).
2. [ ] Configurar cuenta de servicio con permisos necesarios.
3. [ ] Migrar código para usar `langchain-google-vertexai`.
4. [ ] Crear bucket en Cloud Storage para documentos RAG.
5. [ ] Configurar Cloud SQL para persistencia de checkpoints.
6. [ ] Desplegar primera versión en Cloud Run.
7. [ ] Configurar webhook de WhatsApp Business API.
