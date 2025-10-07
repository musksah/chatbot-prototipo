# 🏗️ Arquitectura del Chatbot Cootradecun

## 📊 Diagrama de Flujo Principal

```
┌─────────────────────────────────────────────────────────────────┐
│                         USUARIO                                  │
│                    (Interfaz Web / API)                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ HTTP POST /api/chat
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI SERVER                              │
│                     (app/main.py)                                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ invoke(message)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH CHATBOT                             │
│                   (app/agents/graph.py)                          │
│                                                                  │
│  ┌────────────┐      ┌────────────┐      ┌────────────┐        │
│  │   START    │─────▶│   ROUTER   │─────▶│ call_model │        │
│  └────────────┘      └────────────┘      └─────┬──────┘        │
│                           │                     │                │
│                           │                     │ tool_calls?    │
│                           │                     ▼                │
│                           │              ┌────────────┐          │
│                           │              │   TOOLS    │          │
│                           │              └─────┬──────┘          │
│                           │                    │                 │
│                           │                    │ results         │
│                           │                    ▼                 │
│                           │              ┌────────────┐          │
│                           └─────────────▶│  RESPOND   │          │
│                                          └─────┬──────┘          │
│                                                │                 │
│                                          ┌─────▼──────┐          │
│                                          │    END     │          │
│                                          └────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                           │
                           │ response
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                         USUARIO                                  │
│                  (Respuesta del chatbot)                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Componentes Detallados

### 1. RouterNode (Clasificador de Intenciones)

```
┌─────────────────────────────────────┐
│         RouterNode                  │
│   (app/agents/nodes/router_node.py) │
├─────────────────────────────────────┤
│                                     │
│  Input: "¿Cuáles son los horarios?" │
│                                     │
│  Análisis de palabras clave:        │
│  ├─ "certificado" → certificate     │
│  ├─ "estado/aportes" → linix        │
│  ├─ "crédito" → linix               │
│  ├─ "horario/beneficio" → faq       │
│  └─ default → faq                   │
│                                     │
│  Output: {"route": "faq"}           │
└─────────────────────────────────────┘
```

**Intenciones Soportadas:**
- `certificate` - Generación de certificados
- `linix` - Consultas de estado, aportes, créditos
- `faq` - Preguntas frecuentes, información general
- `default` - Fallback a FAQ

---

### 2. call_model_node (LLM con Tool Calling)

```
┌─────────────────────────────────────────────────────┐
│              call_model_node                        │
│        (app/agents/graph.py)                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Agrega System Prompt                           │
│     ↓                                               │
│  2. Envía mensajes a OpenAI GPT-4o-mini            │
│     ↓                                               │
│  3. El LLM decide:                                  │
│     ├─ Responder directamente                      │
│     └─ Usar una o más tools                        │
│        (rag_search, get_member_status, etc.)       │
│                                                     │
│  Output: AIMessage con posibles tool_calls          │
└─────────────────────────────────────────────────────┘
```

**System Prompt Configurado:**
- Identidad: Asistente de Cootradecun
- Personalidad: Amable, profesional, servicial
- Capacidades: Consultas, simulaciones, certificados
- Restricciones: No inventa datos, pide aclaraciones

---

### 3. ToolNode (Ejecución de Herramientas)

```
┌──────────────────────────────────────────────────────┐
│                    ToolNode                          │
│              (LangGraph ToolNode)                    │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Herramientas Disponibles:                          │
│                                                      │
│  ┌──────────────────────────────────────┐           │
│  │  rag_search                          │           │
│  │  - Búsqueda semántica en ChromaDB   │           │
│  │  - 8 FAQs precargadas               │           │
│  └──────────────────────────────────────┘           │
│                                                      │
│  ┌──────────────────────────────────────┐           │
│  │  get_member_status                   │           │
│  │  - Consulta estado de afiliado       │           │
│  │  - Datos mock de 2 afiliados         │           │
│  └──────────────────────────────────────┘           │
│                                                      │
│  ┌──────────────────────────────────────┐           │
│  │  simulate_credit                     │           │
│  │  - Calcula cuota mensual             │           │
│  │  - Fórmula de amortización           │           │
│  └──────────────────────────────────────┘           │
│                                                      │
│  ┌──────────────────────────────────────┐           │
│  │  check_credit_eligibility            │           │
│  │  - Verifica requisitos               │           │
│  │  - Antigüedad, aportes, cupo         │           │
│  └──────────────────────────────────────┘           │
│                                                      │
│  ┌──────────────────────────────────────┐           │
│  │  generate_certificate                │           │
│  │  - Genera PDF con WeasyPrint         │           │
│  │  - Template Jinja2                   │           │
│  └──────────────────────────────────────┘           │
└──────────────────────────────────────────────────────┘
```

---

### 4. RespondNode (Formateador de Respuestas)

```
┌─────────────────────────────────────────┐
│           RespondNode                   │
│  (app/agents/nodes/respond_node.py)     │
├─────────────────────────────────────────┤
│                                         │
│  1. Extrae último mensaje               │
│  2. Verifica que sea AIMessage          │
│  3. Formatea si es necesario            │
│  4. Agrega emoji 🤖 si falta            │
│                                         │
│  Output: Mensaje formateado para usuario│
└─────────────────────────────────────────┘
```

---

## 🔄 Flujo de Ejecución Completo

### Ejemplo 1: Consulta de Horarios (RAG)

```
1. Usuario: "¿Cuáles son los horarios de atención?"
   ↓
2. RouterNode detecta "horarios" → route = "faq"
   ↓
3. call_model_node:
   - System prompt + mensaje usuario → GPT-4o-mini
   - LLM decide usar rag_search("horarios de atención")
   ↓
4. ToolNode ejecuta rag_search:
   - ChromaDB busca semánticamente
   - Encuentra: "Cootradecun atiende de lunes a viernes..."
   - Retorna resultado
   ↓
5. call_model_node (segunda vez):
   - Recibe resultado de rag_search
   - GPT-4o-mini genera respuesta natural:
     "🤖 Cootradecun atiende de lunes a viernes de 8:00 AM..."
   ↓
6. RespondNode formatea y retorna
   ↓
7. Usuario recibe respuesta completa
```

### Ejemplo 2: Simulación de Crédito

```
1. Usuario: "Simular crédito de 10 millones a 24 meses"
   ↓
2. RouterNode detecta "crédito" → route = "linix"
   ↓
3. call_model_node:
   - GPT-4o-mini extrae: monto=10000000, plazo=24
   - Decide usar simulate_credit(10000000, 24)
   ↓
4. ToolNode ejecuta simulate_credit:
   - Calcula cuota mensual: ~$517,000
   - Calcula intereses totales
   - Retorna simulación completa
   ↓
5. call_model_node:
   - Recibe resultados de la simulación
   - Genera respuesta formateada con los datos
   ↓
6. RespondNode formatea
   ↓
7. Usuario recibe tabla con simulación
```

---

## 🛠️ Stack Tecnológico

```
┌─────────────────────────────────────────────────────┐
│                   Presentación                      │
├─────────────────────────────────────────────────────┤
│  HTML + CSS + JavaScript (Vanilla)                 │
│  - Interfaz moderna y responsive                   │
│  - Fetch API para comunicación                     │
└─────────────────────────────────────────────────────┘
                        │
                        │ HTTP
                        ▼
┌─────────────────────────────────────────────────────┐
│                   API Layer                         │
├─────────────────────────────────────────────────────┤
│  FastAPI 0.109.0                                    │
│  - Endpoints REST                                   │
│  - Validación con Pydantic                         │
│  - Documentación automática (Swagger)              │
└─────────────────────────────────────────────────────┘
                        │
                        │ invoke()
                        ▼
┌─────────────────────────────────────────────────────┐
│                 Orchestration Layer                 │
├─────────────────────────────────────────────────────┤
│  LangGraph 0.0.20                                   │
│  - StateGraph para flujo                           │
│  - ToolNode para herramientas                      │
│  - Conditional edges                               │
└─────────────────────────────────────────────────────┘
                        │
                        │ call LLM
                        ▼
┌─────────────────────────────────────────────────────┐
│                   LLM Layer                         │
├─────────────────────────────────────────────────────┤
│  OpenAI GPT-4o-mini                                 │
│  - Tool calling automático                         │
│  - Generación de respuestas                        │
│  - Extracción de parámetros                        │
└─────────────────────────────────────────────────────┘
            │                    │
            │                    │
    ┌───────▼──────┐      ┌─────▼────────┐
    │   ChromaDB   │      │  Mock Linix  │
    │   (Vector)   │      │   (Python)   │
    │              │      │              │
    │  8 FAQs      │      │  2 afiliados │
    └──────────────┘      └──────────────┘
```

---

## 📦 Estructura de Datos

### MessagesState (LangGraph)

```python
{
    "messages": [
        HumanMessage(content="¿Cuáles son los horarios?"),
        SystemMessage(content="Eres un asistente..."),
        AIMessage(content="...", tool_calls=[...]),
        ToolMessage(content="...", tool_call_id="..."),
        AIMessage(content="🤖 Respuesta final")
    ],
    "route": "faq"  # Agregado por RouterNode
}
```

### Tool Call Format (OpenAI)

```python
{
    "id": "call_abc123",
    "type": "function",
    "function": {
        "name": "rag_search",
        "arguments": '{"query": "horarios", "top_k": 3}'
    }
}
```

### Tool Response Format

```python
{
    "success": True,
    "found": True,
    "answer": "Cootradecun atiende de lunes...",
    "sources": ["faq_1"],
    "all_passages": [...]
}
```

---

## 🔐 Flujo de Seguridad

```
┌─────────────────────────────────────────┐
│  Configuración de Seguridad             │
├─────────────────────────────────────────┤
│                                         │
│  ✅ API Key en .env (no commiteada)    │
│  ✅ CORS configurado (puede restringir)│
│  ✅ No se loguean datos personales     │
│  ✅ Validación con Pydantic            │
│  ✅ Datos mock (no datos reales)       │
│                                         │
│  ⚠️  Faltante (para producción):       │
│     - Autenticación de usuarios        │
│     - Rate limiting                    │
│     - Encriptación de datos            │
│     - Auditoría de accesos             │
└─────────────────────────────────────────┘
```

---

## 📊 Logging y Observabilidad

```
┌─────────────────────────────────────────────────────┐
│                  Logging Strategy                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Nivel INFO:                                        │
│  ├─ Mensaje recibido (truncado a 100 chars)        │
│  ├─ Ruta detectada por router                      │
│  ├─ Tool calls realizados (nombre + args)          │
│  ├─ Respuesta generada (truncada)                  │
│  └─ Tiempo de procesamiento                        │
│                                                     │
│  Nivel ERROR:                                       │
│  ├─ Errores de API                                 │
│  ├─ Fallos en tools                                │
│  ├─ Excepciones no capturadas                      │
│  └─ Stack traces                                   │
│                                                     │
│  Formato:                                           │
│  timestamp - module - level - message               │
└─────────────────────────────────────────────────────┘
```

---

## 🔄 Escalabilidad y Extensibilidad

### Agregar Nueva Tool

1. Crear archivo en `app/agents/tools/`
2. Decorar función con `@tool("nombre")`
3. Agregar descripción clara
4. Importar en `graph.py`
5. Agregar a lista `tools`

### Agregar Nueva Ruta

1. Modificar `router_node.py`
2. Agregar palabras clave
3. Retornar nueva ruta
4. Configurar edge condicional en `graph.py`

### Agregar Nueva FAQ

1. Editar `_load_sample_data()` en `rag_tool.py`
2. Agregar dict con id, text, metadata
3. Reiniciar servidor (ChromaDB in-memory se recarga)

---

## 🎯 Decisiones de Diseño

### ¿Por qué RouterNode antes del LLM?

**Ventajas:**
- ✅ Clasificación rápida sin llamada a LLM
- ✅ Ahorro de tokens
- ✅ Control determinista
- ✅ Fácil debugging

**Alternativa:** Dejar que el LLM decida todo
- ❌ Más lento
- ❌ Más costoso
- ❌ Menos predecible

### ¿Por qué ChromaDB in-memory?

**Para MVP:**
- ✅ Simple, sin configuración
- ✅ Rápido para 8 FAQs
- ✅ No requiere persistencia

**Para Producción:**
- Cambiar a ChromaDB persistente
- Considerar Pinecone/Weaviate

### ¿Por qué datos Mock?

**Para Demo:**
- ✅ No requiere API real de Linix
- ✅ Resultados consistentes
- ✅ Fácil de probar
- ✅ Sin dependencias externas

---

## 📈 Métricas de Performance

```
Métrica                    | Valor Esperado
---------------------------|------------------
Tiempo de respuesta        | 1-3 segundos
Llamadas a OpenAI por msg  | 1-2 (depende tools)
Tokens por mensaje         | 200-1000
Costo por 1000 mensajes    | ~$0.50 (GPT-4o-mini)
Memoria RAM                | ~150 MB
CPU en idle                | <5%
```

---

## 🚀 Despliegue

### Local (Desarrollo)
```bash
python run.py
```

### Docker (Futuro)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Cloud (Producción)
- **Heroku:** Dyno con worker
- **AWS:** Lambda + API Gateway
- **GCP:** Cloud Run
- **Azure:** App Service

---

## 📚 Referencias

- **LangGraph:** https://langchain-ai.github.io/langgraph/
- **FastAPI:** https://fastapi.tiangolo.com/
- **OpenAI:** https://platform.openai.com/docs/
- **ChromaDB:** https://docs.trychroma.com/

---

*Diagrama actualizado: Octubre 2025*

