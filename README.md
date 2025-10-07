# Chatbot Cootradecun - Prototipo MVP

Prototipo funcional de chatbot para la cooperativa Cootradecun usando arquitectura **LangGraph Router + Tool Calling** con OpenAI GPT-4o-mini.

## 🧱 Stack Tecnológico

- **Python 3.11**
- **FastAPI** - API REST y servidor web
- **LangGraph + LangChain** - Orquestación de agentes y tool calling
- **OpenAI GPT-4o-mini** - Modelo de lenguaje
- **ChromaDB** - Base de datos vectorial para RAG
- **SQLite** - Persistencia ligera
- **WeasyPrint + Jinja2** - Generación de PDFs

## 📁 Estructura del Proyecto

```
mvp-chatbot-cootradecun/
├── app/
│   ├── main.py                    # FastAPI app principal
│   ├── routers/
│   │   └── chat.py                # Endpoints del chat
│   ├── agents/
│   │   ├── graph.py               # Grafo LangGraph principal
│   │   ├── nodes/
│   │   │   ├── router_node.py     # Nodo de routing
│   │   │   └── respond_node.py    # Nodo de respuesta
│   │   └── tools/
│   │       ├── rag_tool.py        # Herramienta RAG
│   │       ├── linix_tools.py     # Herramientas mock Linix
│   │       └── certificate_tool.py # Generación de certificados
│   ├── templates/
│   │   └── chat.html              # Interfaz web del chat
│   ├── static/                    # Archivos estáticos (CSS, JS)
│   └── data/                      # Datos de ejemplo
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 Instalación

1. **Clonar el repositorio**
   ```bash
   cd mvp-chatbot-cootradecun
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env y agregar tu OPENAI_API_KEY
   ```

## 🔧 Configuración

Crear un archivo `.env` con:

```
OPENAI_API_KEY=tu_api_key_aqui
ENVIRONMENT=development
```

## ▶️ Ejecución

### Opción 1: Script de inicio (Recomendado)

**Windows:**
```cmd
run.bat
```

**Windows/Linux/Mac:**
```bash
python run.py
```

### Opción 2: Uvicorn directamente

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Opción 3: Con Python

```bash
python -m app.main
```

Acceder a: http://localhost:8000

## 🧪 Funcionalidades

### 1. **Router Inteligente**
Clasifica automáticamente las consultas en:
- 📚 **FAQ**: Preguntas frecuentes sobre servicios
- 💼 **Linix**: Consultas de estado de afiliación, aportes, simulación de créditos
- 📄 **Certificados**: Generación de certificados de afiliación

### 2. **Tool Calling**
- `rag_search`: Búsqueda semántica en base de conocimiento
- `get_member_status`: Consulta estado de afiliado (mock)
- `simulate_credit`: Simulación de créditos (mock)
- `generate_certificate`: Generación de certificados PDF

### 3. **Base de Conocimiento desde Markdown**
- FAQs cargados dinámicamente desde `app/data/faqs_cootradecun.md`
- Fácil de editar sin tocar código Python
- 12 FAQs precargados y listos para usar
- Ver [COMO_AGREGAR_FAQS.md](docs/COMO_AGREGAR_FAQS.md) para detalles

### 4. **Memoria de Conversaciones**
- Mantiene el contexto de conversaciones por sesión
- Soporta múltiples usuarios simultáneos con sesiones independientes
- Sistema de checkpointing de LangGraph
- Ver [MEMORIA_CONVERSACIONES.md](docs/MEMORIA_CONVERSACIONES.md) para detalles

### 5. **Restricciones de Contexto** ✨ NUEVO
- El bot SOLO responde preguntas sobre Cootradecun
- Rechaza cortésmente preguntas fuera de contexto (recetas, deportes, etc.)
- Mantiene el foco en servicios cooperativos
- Ver [RESTRICCIONES_CHATBOT.md](docs/RESTRICCIONES_CHATBOT.md) para detalles

### 6. **Interfaz Web**
Interfaz simple y moderna para interactuar con el chatbot.

## 🧠 Arquitectura

```
User Input → RouterNode → call_model_with_tools → ToolNode → RespondNode → Output
```

1. **RouterNode**: Clasifica la intención del usuario
2. **call_model_with_tools**: El LLM decide qué herramientas usar
3. **ToolNode**: Ejecuta la herramienta seleccionada
4. **RespondNode**: Formatea y devuelve la respuesta

## 📝 Ejemplos de Uso

- "¿Cuáles son los horarios de atención?"
- "¿Cuál es el estado de mis aportes?"
- "Quiero simular un crédito de 10 millones"
- "Necesito un certificado de afiliación"

## 🔐 Seguridad

- No se almacenan datos personales en logs
- Las consultas mock no acceden a datos reales
- Variables sensibles en `.env` (no commitear)

## 🔧 Solución de Problemas

### Error: UnicodeDecodeError al cargar .env
**Solución rápida:**
```cmd
create_env.bat
```
Este script crea el archivo `.env` con la codificación correcta (UTF-8).

### Otros problemas comunes
Consulta la [Guía de Solución de Problemas](docs/TROUBLESHOOTING.md) para:
- Errores de codificación
- Problemas con módulos
- Puerto en uso
- Instalación de WeasyPrint en Windows
- Y más...

## 📚 Documentación Completa

Toda la documentación está organizada en la carpeta [docs/](docs/):

- **[QUICKSTART.md](docs/QUICKSTART.md)** - Inicio rápido en 3 pasos
- **[INSTALL.md](docs/INSTALL.md)** - Guía de instalación detallada
- **[COMO_AGREGAR_FAQS.md](docs/COMO_AGREGAR_FAQS.md)** - Cómo agregar/editar FAQs
- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Solución de problemas
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Arquitectura técnica
- **[PROYECTO_COMPLETADO.md](docs/PROYECTO_COMPLETADO.md)** - Resumen del proyecto

Ver el [índice completo de documentación](docs/README.md).

## 📅 Desarrollo

Este es un **prototipo MVP** desarrollado en 3 semanas como demostración técnica para la cooperativa Cootradecun.

## 🤝 Contribución

Prototipo interno. Para sugerencias, contactar al equipo de desarrollo.

