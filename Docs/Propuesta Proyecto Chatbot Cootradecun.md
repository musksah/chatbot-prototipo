# Propuesta Técnica y Comercial: Asistente de IA Conversacional "Cootradecun Inteligente"

## 1. Introducción y Objetivo

El presente proyecto busca transformar la interacción de los asociados con la cooperativa, sustituyendo flujos de decisión rígidos por un **Agente de Inteligencia Artificial de Lenguaje Natural**. El sistema será capaz de entender consultas complejas y gestionar trámites en un entorno de conversación fluida, aumentando la eficiencia operativa y la satisfacción del usuario final.

---

## 2. Alcance del Proyecto

El alcance se limita estrictamente a las funcionalidades descritas en este documento, cubriendo la atención automatizada para los siguientes **8 departamentos/áreas clave**:

1. Atención al Asociado
2. Cartera
3. Convenios
4. Nóminas
5. Vivienda
6. Créditos
7. Contabilidad
8. Tesorería

### Funcionalidades de la Aplicación Administrativa (Dashboard)

El proyecto incluirá una aplicación administrativa (Dashboard) con las siguientes funcionalidades para la gestión interna del sistema:

#### Módulo de Reportes y Monitoreo
- Cantidad de usuarios activos
- Cantidad de conversaciones por fecha
- Temas más consultados (análisis de intents)
- Módulo de uso de tokens (para monitoreo de costos LLM)

#### Módulo RAG (Generación Aumentada por Recuperación)
- Interfaz para el manejo y actualización de archivos de la base de conocimiento (documentos, políticas, etc.) por parte del usuario administrador

#### Módulo de Usuarios y Seguridad
- Gestión de Usuarios, Roles y permisos de la aplicación administrativa

### Fase 1: Implementación del Cerebro Cognitivo (Q&A)

- Despliegue de un sistema **RAG (Retrieval-Augmented Generation)** para responder preguntas basadas en la normativa de los 8 departamentos mencionados
- Configuración de agentes LLM para una conversación natural y fluida en WhatsApp
- Guía hacia funcionalidades web existentes (Actualización de datos, Simuladores, Pagos)

### Fase 2: Integración Transaccional y Certificados

- Implementación de autenticación obligatoria mediante **Código de Un Solo Uso (OTP)** vía WhatsApp, SMS o Correo
- Conexión con WebServices para la generación y envío automático de certificados:
  - Estados de cuenta
  - Paz y salvo
  - Cartera
  - Tributarios
  - Ahorros y Aportes

> [!NOTE]
> Esta fase depende de la entrega de APIs por parte del proveedor externo de la cooperativa.

---

## 3. Arquitectura Tecnológica (Ecosistema GCP)

La solución se ejecutará en la infraestructura de **Google Cloud Platform**, garantizando una disponibilidad del **99.9%**.

| Componente | Tecnología |
|------------|------------|
| **Cómputo** | Cloud Run para el backend (FastAPI + LangGraph) |
| **Inteligencia** | Vertex AI (Gemini 1.5) y Vertex AI Embeddings |
| **Búsqueda** | Vertex AI Vector Search para la base de conocimientos RAG |
| **Seguridad** | Secret Manager para el resguardo de llaves y Cloud Armor para protección perimetral |
| **Persistencia** | Cloud SQL (PostgreSQL) para historiales y checkpoints de conversación |

---

## 4. Propuesta Económica

### 4.1. Inversión Inicial (Desarrollo e Implementación)

Este valor cubre la ingeniería de prompts, configuración de infraestructura y desarrollo asistido por IA (Antigravity + Gemini).

| Concepto | Valor |
|----------|-------|
| Implementación Fase 1 (Q&A) | **$15.000.000 COP** |
| Implementación Fase 2 (Transaccional) | **$10.000.000 COP** |
| **Total Inversión** | **$25.000.000 COP** |

### 4.2. Costos Mensuales de Operación y Licenciamiento

| Concepto | Tipo | Valor Sugerido |
|----------|------|----------------|
| Licencia Dashboard Admin | Fijo | $900.000 COP |
| Procesamiento de IA (Tokens) | Variable | $25 USD / 1M tokens |
| Hosting GCP (Proyecto Cliente) | Variable | ~$50 - $100 USD (Est. según uso) |

### 4.3. Gestión de Canal WhatsApp (Tarifas Meta 2026)

El cobro por la mensajería se ajusta al modelo de Meta basado en categorías de conversación y una ventana de 24 horas, priorizando la **Cloud API directa de Meta** para eliminar costos de intermediarios (BSP).

#### Tarifas Meta para Colombia (2026)

| Categoría | Propósito | Costo (USD) | Costo (COP) |
|-----------|-----------|-------------|-------------|
| **Servicio** | Consultas iniciadas por el asociado | Gratis (primeras 500) | $0 COP |
| **Utilidad** | Estados de cuenta, confirmaciones, alertas | $0.0009 | ~$4 COP |
| **Autenticación** | Códigos OTP (SMS-like) para seguridad | $0.0077 | ~$31 COP |
| **Marketing** | Promociones, ofertas, novedades | $0.0144 | ~$58 COP |

> [!IMPORTANT]
> Los valores presentados en dólares estadounidenses (USD) están sujetos a la Tasa Representativa del Mercado (TRM) vigente al momento de la facturación. Asimismo, las tarifas de mensajería podrán ajustarse en caso de cambios en la estructura de costos oficiales de Meta Business API.

#### Ejemplo de Costo Mensual (Escenario Mixto: 3,000 conversaciones)

Si la cooperativa genera un total de 3,000 conversaciones al mes:
- 2,000 de Servicio (1,000 gratuitas por mes + 1,000 con costo mínimo)
- 500 de Autenticación (OTP)
- 500 de Utilidad

**Costo estimado:**

| Categoría | Cálculo | Total |
|-----------|---------|-------|
| Autenticación | 500 × $0.0077 USD | $3.85 USD |
| Utilidad | 500 × $0.0009 USD | $0.45 USD |
| **Total estimado** | | **$4.30 USD (~$17.200 COP)** |

> Este valor es independiente del consumo de tokens de IA.

---

## 5. Términos y Condiciones

### 5.1. Alcance y Exclusiones

- El alcance del proyecto se limita exclusivamente a lo relacionado en este documento para los 8 departamentos definidos.
- **Cualquier funcionalidad, integración o departamento adicional** no listado en esta propuesta tendrá un costo adicional. Dichos requerimientos serán evaluados y facturados por horas de trabajo técnico, previo acuerdo entre las partes.

### 5.2. Propiedad Intelectual y Licenciamiento

- **Cootradecun es propietaria** de los datos almacenados en su proyecto de GCP.
- El Dashboard Administrativo se entrega bajo una **licencia de uso mensual**; el código base y la plataforma son propiedad del proveedor.

### 5.3. Responsabilidades de Terceros

- La ejecución de la Fase 2 está sujeta a la entrega oportuna y funcional de los WebServices por parte del proveedor tecnológico actual de la cooperativa. Retrasos ajenos al desarrollador no afectarán los cronogramas de pago de la Fase 1.

### 5.4. Soporte y Garantía

- Se incluye **soporte técnico preventivo** sobre la infraestructura desplegada mientras la licencia del Dashboard esté vigente.
- La garantía cubre defectos de fabricación del software por un periodo de **3 meses** tras la entrega final.
