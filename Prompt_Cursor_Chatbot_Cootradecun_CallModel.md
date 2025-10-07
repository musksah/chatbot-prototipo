# PROMPT PARA CURSOR — Prototipo Chatbot Cootradecun (3 Semanas)
### Arquitectura **Router** + **Tool Calling** (con `call_model` y OpenAI GPT-4o-mini)

Quiero que crees un **prototipo funcional del chatbot de Cootradecun**,  
siguiendo la arquitectura de **LangGraph Router + Tool Calling** y el patrón más reciente descrito en este artículo:  
👉 https://medium.com/@vivekvjnk/introduction-to-tool-use-with-langgraphs-toolnode-0121f3c8c323  

El objetivo es construir un **proyecto ejecutable localmente (3 semanas)** que demuestre:
- Flujo **Router → Tool Calling → Response**.  
- Uso del método `call_model()` con **OpenAI GPT-4o-mini**.  
- Ejecución tipada de herramientas (RAG, Linix mock, generación de PDFs).  
- Interfaz web simple para interacción (sin WhatsApp real).  

---

## 🧱 Stack
- **Python 3.11**  
- **FastAPI** (API y UI simple)  
- **LangGraph** + **LangChain OpenAI** (Router + Tool Calling)  
- **ChromaDB** (RAG local, in-memory)  
- **SQLite** (persistencia ligera)  
- **WeasyPrint** + **Jinja2** (PDFs simulados)  

---

## 📁 Estructura esperada
```
cootradecun-proto/
  app/
    main.py
    routers/chat.py
    agents/
      graph.py
      nodes/
        router_node.py
        respond_node.py
      tools/
        rag_tool.py
        linix_tools.py
        certificate_tool.py
```

---

## 🧠 Ejemplo actualizado de `graph.py`
Usa el **patrón call_model()** como se explica en el artículo.

```python
# app/agents/graph.py
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langgraph.utils import call_model

# Importar las tools definidas
from .tools.rag_tool import rag_search
from .tools.linix_tools import get_member_status, simulate_credit
from .tools.certificate_tool import generate_certificate
from .nodes.router_node import router_node
from .nodes.respond_node import respond_node

# 1️⃣ Crear modelo base (OpenAI GPT-4o-mini)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 2️⃣ Registrar herramientas disponibles
tools = [rag_search, get_member_status, simulate_credit, generate_certificate]

# 3️⃣ Crear función call_model (manejo del Tool Calling)
def call_model_with_tools(state: MessagesState):
    '''
    Ejecuta el modelo con capacidad de Tool Calling.
    Usa el contexto conversacional de 'state' y decide si llamar una tool.
    '''
    return call_model(llm, state, tools=tools)

# 4️⃣ Nodo para ejecución de herramientas (ToolNode)
tool_node = ToolNode(tools=tools)

# 5️⃣ Construcción del grafo Router → ToolCall → Respond
graph = StateGraph(MessagesState)

graph.add_node("router", router_node(llm))
graph.add_node("llm_call", call_model_with_tools)
graph.add_node("tool_node", tool_node)
graph.add_node("respond", respond_node)

# Transiciones
graph.add_edge(START, "router")
graph.add_conditional_edges("router", {
    "faq": "llm_call",
    "linix": "llm_call",
    "certificate": "llm_call",
    "default": "respond",
})
graph.add_edge("llm_call", "tool_node")
graph.add_edge("tool_node", "respond")
graph.add_edge("respond", END)

chatbot_graph = graph.compile()
```

---

## ⚒️ Ejemplo de Tool (`rag_tool.py`)

```python
# app/agents/tools/rag_tool.py
from typing import Dict
from langchain.tools import tool
from chromadb import Client

@tool("rag_search", return_direct=False)
def rag_search(query: str, top_k: int = 3) -> Dict:
    '''Busca información en la base Chroma local.'''
    client = Client()
    collection = client.get_or_create_collection("cootradecun_faqs")
    results = collection.query(query_texts=[query], n_results=top_k)
    passages = results["documents"][0]
    return {"answer": passages[0], "sources": results["ids"][0]}
```

---

## 🔀 RouterNode (`router_node.py`)
```python
# app/agents/nodes/router_node.py
from typing import Dict

def router_node(llm):
    def route(state: Dict) -> Dict:
        text = state["input"].lower()
        if "certificado" in text or "afiliación" in text:
            return {"next": "certificate"}
        elif "estado" in text or "aportes" in text:
            return {"next": "linix"}
        elif "crédito" in text or "cuota" in text:
            return {"next": "linix"}
        elif "horario" in text or "beneficio" in text:
            return {"next": "faq"}
        else:
            return {"next": "default"}
    return route
```

---

## 💬 RespondNode (`respond_node.py`)
```python
# app/agents/nodes/respond_node.py
def respond_node(state):
    '''Formatea la salida para mostrarla en el chat.'''
    if "output" in state:
        return {"response": f"🤖 {state['output']}"}
    return {"response": "🤖 No encontré información. Intenta con otra pregunta."}
```

---

## 🧩 Flujo general
```
User → RouterNode → call_model_with_tools → ToolNode → RespondNode → Output
```

- **RouterNode** decide la intención (faq, linix, certificado, default).  
- **call_model_with_tools** ejecuta el modelo con Tool Calling.  
- El **LLM decide** si invocar una tool (`rag_search`, `generate_certificate`, etc.).  
- **ToolNode** ejecuta la herramienta seleccionada.  
- **RespondNode** resume y responde al usuario.  

---

## ✅ Buenas prácticas
- Todas las tools deben usar `@tool` con nombre y descripción.  
- Mantener **logs por cada Tool Call** (`tool_name`, `args`, `duration`).  
- Las respuestas deben ser **claras, cortas y conversacionales**.  
- No incluir datos personales en los logs.  

---

## 🚀 Objetivo
Entregar en 3 semanas un **prototipo ejecutable** que:
1. Use LangGraph Router + Tool Calling (con `call_model`).  
2. Ejecute herramientas reales (RAG, PDF simulado, mock Linix).  
3. Tenga una interfaz HTML simple (`chat.html`) para pruebas.  
4. Sirva como **demo convincente** para la cooperativa Cootradecun.
