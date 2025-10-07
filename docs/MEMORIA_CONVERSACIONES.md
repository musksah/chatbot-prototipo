# 🧠 Memoria de Conversaciones - Chatbot Cootradecun

## 📋 Descripción General

El chatbot ahora incluye **memoria persistente de conversaciones** utilizando el sistema de checkpointing de LangGraph. Esto permite que el chatbot mantenga el contexto de conversaciones anteriores dentro de una misma sesión.

---

## ✨ Características

### 1. **Memoria por Sesión**
- Cada usuario tiene un `session_id` único
- El chatbot recuerda todo el contexto de la conversación dentro de esa sesión
- Las conversaciones de diferentes usuarios están completamente aisladas

### 2. **Persistencia Automática**
- No necesitas hacer nada especial, la memoria se guarda automáticamente
- Cada mensaje y respuesta se almacenan en el checkpoint
- El estado se mantiene mientras el servidor esté corriendo

### 3. **Multi-Sesión**
- Soporta múltiples conversaciones simultáneas
- Cada `session_id` mantiene su propio contexto independiente

---

## 🔧 Implementación Técnica

### Checkpointer

Utilizamos `MemorySaver` de LangGraph:

```python
from langgraph.checkpoint.memory import MemorySaver

# Crear checkpointer
memory_checkpointer = MemorySaver()

# Compilar grafo con checkpointer
chatbot_graph = graph.compile(checkpointer=memory_checkpointer)
```

### Configuración por Sesión

Al invocar el grafo, pasamos el `session_id` como `thread_id`:

```python
config = {
    "configurable": {
        "thread_id": session_id  # ID único de la sesión
    }
}

result = chatbot_graph.invoke(input_state, config)
```

---

## 🚀 Uso

### Desde la API

**Enviar Mensaje:**

```bash
POST /api/chat
Content-Type: application/json

{
  "message": "Hola, mi nombre es Juan",
  "session_id": "user123"
}
```

**Respuesta:**
```json
{
  "response": "¡Hola Juan! ¿En qué puedo ayudarte hoy?",
  "session_id": "user123",
  "timestamp": "2024-10-07T10:30:00",
  "processing_time": 1.23
}
```

**Mensaje de Seguimiento:**

```bash
POST /api/chat
Content-Type: application/json

{
  "message": "¿Recuerdas mi nombre?",
  "session_id": "user123"
}
```

**Respuesta:**
```json
{
  "response": "¡Claro que sí, Juan! ¿Cómo te puedo ayudar?",
  "session_id": "user123",
  "timestamp": "2024-10-07T10:31:00",
  "processing_time": 0.98
}
```

---

## 📊 Endpoints de Gestión

### 1. Ver Historial de una Sesión

```bash
GET /api/chat/history/{session_id}
```

**Respuesta:**
```json
{
  "session_id": "user123",
  "message_count": 4,
  "messages": [
    {
      "type": "HumanMessage",
      "content": "Hola, mi nombre es Juan",
      "role": "user"
    },
    {
      "type": "AIMessage",
      "content": "¡Hola Juan! ¿En qué puedo ayudarte hoy?",
      "role": "assistant"
    }
  ],
  "has_state": true
}
```

### 2. Limpiar Historial de una Sesión

```bash
DELETE /api/chat/history/{session_id}
```

**Respuesta:**
```json
{
  "success": true,
  "session_id": "user123",
  "messages_deleted": 4,
  "message": "Historial limpiado exitosamente (4 mensajes eliminados)"
}
```

### 3. Listar Sesiones Activas

```bash
GET /api/chat/sessions
```

**Nota:** El `MemorySaver` in-memory no expone todas las sesiones directamente. Para producción, considera usar `SqliteSaver` o `PostgresSaver`.

---

## 💡 Ejemplos de Uso

### Ejemplo 1: Conversación Contextual

```bash
# Mensaje 1
POST /api/chat
{
  "message": "Quiero solicitar un crédito",
  "session_id": "user456"
}

# Respuesta: El bot pregunta detalles

# Mensaje 2 (el bot recuerda el contexto)
POST /api/chat
{
  "message": "De 5 millones a 12 meses",
  "session_id": "user456"
}

# Respuesta: El bot calcula el crédito usando los datos proporcionados
```

### Ejemplo 2: Múltiples Usuarios Simultáneos

```bash
# Usuario 1
POST /api/chat
{
  "message": "Mi nombre es María",
  "session_id": "user_maria"
}

# Usuario 2 (conversación independiente)
POST /api/chat
{
  "message": "Mi nombre es Pedro",
  "session_id": "user_pedro"
}

# Usuario 1 continúa
POST /api/chat
{
  "message": "¿Recuerdas mi nombre?",
  "session_id": "user_maria"
}
# Respuesta: "Sí, María..."

# Usuario 2 continúa
POST /api/chat
{
  "message": "¿Recuerdas mi nombre?",
  "session_id": "user_pedro"
}
# Respuesta: "Sí, Pedro..."
```

---

## ⚙️ Configuración Avanzada

### Cambiar a SQLite (Persistencia en Disco)

Para memoria que persista entre reinicios del servidor:

1. Instalar dependencia:
```bash
pip install aiosqlite
```

2. Modificar `app/agents/graph.py`:

```python
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# Crear checkpointer con SQLite
memory_checkpointer = AsyncSqliteSaver.from_conn_string("checkpoints.db")

# El resto del código permanece igual
```

### Cambiar a PostgreSQL (Producción)

Para entornos de producción con múltiples servidores:

1. Instalar dependencia:
```bash
pip install psycopg2-binary
```

2. Modificar `app/agents/graph.py`:

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# Crear checkpointer con PostgreSQL
memory_checkpointer = AsyncPostgresSaver.from_conn_string(
    "postgresql://user:password@localhost:5432/chatbot_db"
)
```

---

## 🔍 Inspeccionar el Estado

Puedes inspeccionar el estado completo de una sesión:

```python
from app.agents.graph import chatbot_graph

config = {"configurable": {"thread_id": "user123"}}
state = chatbot_graph.get_state(config)

print(state.values)  # Estado completo
print(state.next)    # Próximo nodo a ejecutar
print(state.config)  # Configuración utilizada
```

---

## 📈 Beneficios

### ✅ Para el Usuario
- Conversaciones más naturales y contextuales
- No necesita repetir información
- El bot "recuerda" detalles importantes
- Experiencia más personalizada

### ✅ Para el Sistema
- Mejor entendimiento del contexto
- Reduce ambigüedades
- Permite conversaciones complejas multi-turno
- Facilita workflows de múltiples pasos

---

## ⚠️ Limitaciones Actuales

### MemorySaver (In-Memory)

1. **No persiste entre reinicios**
   - Si se reinicia el servidor, se pierden todas las sesiones
   - Solución: Usar SqliteSaver o PostgresSaver

2. **No escalable horizontalmente**
   - Si tienes múltiples servidores, cada uno tiene su propia memoria
   - Solución: Usar PostgresSaver con base de datos compartida

3. **Sin límite de memoria**
   - Las conversaciones muy largas pueden consumir mucha RAM
   - Solución: Implementar limpieza automática de sesiones antiguas

---

## 🧪 Pruebas

### Script de Prueba Manual

```python
import requests

BASE_URL = "http://localhost:8000/api"
SESSION_ID = "test_memory"

# Mensaje 1
response = requests.post(f"{BASE_URL}/chat", json={
    "message": "Hola, mi nombre es Carlos",
    "session_id": SESSION_ID
})
print(response.json()["response"])

# Mensaje 2 (debe recordar el nombre)
response = requests.post(f"{BASE_URL}/chat", json={
    "message": "¿Recuerdas mi nombre?",
    "session_id": SESSION_ID
})
print(response.json()["response"])  # Debe mencionar "Carlos"

# Ver historial
response = requests.get(f"{BASE_URL}/chat/history/{SESSION_ID}")
print(response.json())

# Limpiar historial
response = requests.delete(f"{BASE_URL}/chat/history/{SESSION_ID}")
print(response.json())
```

---

## 📚 Referencias

- [LangGraph Memory Tutorial](https://langchain-ai.github.io/langgraph/tutorials/get-started/3-add-memory/)
- [LangGraph Checkpointing](https://langchain-ai.github.io/langgraph/how-tos/persistence/)
- [AsyncSqliteSaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.sqlite.aio.AsyncSqliteSaver)
- [AsyncPostgresSaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.postgres.aio.AsyncPostgresSaver)

---

## 🎯 Próximos Pasos

1. **Implementar limpieza automática** de sesiones inactivas después de X tiempo
2. **Migrar a SqliteSaver** para persistencia en disco
3. **Agregar métricas** de uso de memoria por sesión
4. **Implementar exportación** del historial a formato JSON/CSV
5. **Agregar límite de mensajes** por sesión (ej: últimos 50 mensajes)

---

*Última actualización: Octubre 2025*
*Versión del chatbot: 1.1.0*

