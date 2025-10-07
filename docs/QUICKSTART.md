# 🚀 Inicio Rápido - Chatbot Cootradecun

## ⚡ Primeros 3 Pasos

### 1. Configurar API Key de OpenAI

Crea un archivo `.env` en la raíz del proyecto:

```bash
OPENAI_API_KEY=sk-tu-api-key-aqui
```

### 2. Instalar dependencias

```bash
# Activar entorno virtual (recomendado)
python -m venv venv
.\venv\Scripts\Activate  # Windows PowerShell
# o
source venv/bin/activate  # Linux/Mac

# Instalar paquetes
pip install -r requirements.txt
```

### 3. Ejecutar el chatbot

**En Windows:**
```cmd
run.bat
```

**O con Python (Windows/Linux/Mac):**
```bash
python run.py
```

Abre tu navegador en: **http://localhost:8000**

## 🎯 Ejemplos de Prueba

Una vez que el chatbot esté corriendo, prueba estas consultas:

### 1. Información General (FAQ)
```
¿Cuáles son los horarios de atención?
```
```
¿Qué beneficios tiene ser afiliado a Cootradecun?
```

### 2. Consulta de Estado (Mock Linix)
```
¿Cuál es el estado del afiliado con cédula 12345678?
```
```
Consultar aportes del afiliado 87654321
```

### 3. Simulación de Créditos
```
Quiero simular un crédito de 10 millones a 24 meses
```
```
Simular crédito de 5000000 pesos a 12 meses
```

### 4. Generación de Certificados
```
Necesito un certificado de afiliación para la cédula 12345678
```
```
Generar certificado para 87654321
```

## 📊 Arquitectura del Flujo

```
Usuario ingresa mensaje
    ↓
RouterNode (clasifica intención)
    ↓
call_model_with_tools (GPT-4o-mini decide si usar tools)
    ↓
ToolNode (ejecuta la herramienta seleccionada)
    ↓
RespondNode (formatea la respuesta)
    ↓
Respuesta al usuario
```

## 🛠️ Herramientas Disponibles

1. **rag_search** - Búsqueda en base de conocimiento (8 FAQs cargadas)
2. **get_member_status** - Consulta estado de afiliado (2 afiliados mock)
3. **simulate_credit** - Simulación de créditos con cálculo de cuotas
4. **check_credit_eligibility** - Verificación de elegibilidad para créditos
5. **generate_certificate** - Generación de certificados PDF

## 🧪 Probar sin Interfaz Web

### Opción 1: Script de pruebas

```bash
python test_chatbot.py
```

### Opción 2: API directamente (PowerShell)

```powershell
$body = @{
    message = "Hola"
    session_id = "test"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/chat" -Method POST -Body $body -ContentType "application/json"
```

### Opción 3: Documentación interactiva

Abre http://localhost:8000/docs y prueba los endpoints directamente desde Swagger UI.

## 📁 Estructura del Proyecto

```
mvp-chatbot-cootradecun/
├── app/
│   ├── main.py                      # FastAPI app
│   ├── agents/
│   │   ├── graph.py                 # Grafo LangGraph principal ⭐
│   │   ├── nodes/
│   │   │   ├── router_node.py       # Clasificador de intenciones
│   │   │   └── respond_node.py      # Formateador de respuestas
│   │   └── tools/
│   │       ├── rag_tool.py          # Búsqueda semántica
│   │       ├── linix_tools.py       # Mock sistema Linix
│   │       └── certificate_tool.py  # Generación PDFs
│   ├── routers/
│   │   └── chat.py                  # Endpoints del chat
│   ├── templates/
│   │   └── chat.html                # Interfaz web
│   └── static/
├── requirements.txt                 # Dependencias
├── run.py                          # Script de inicio ⭐
├── test_chatbot.py                 # Script de pruebas
└── .env                            # Configuración (crear manualmente)
```

## 🔧 Configuración Adicional

### Cambiar Puerto

En `.env`:
```
PORT=8001
```

### Cambiar Modelo

En `app/agents/graph.py`:
```python
llm = ChatOpenAI(
    model="gpt-4o-mini",  # Cambiar a "gpt-4" si prefieres
    temperature=0.3,
)
```

### Agregar más FAQs

Edita `app/agents/tools/rag_tool.py` en la función `_load_sample_data()`.

### Agregar más Afiliados Mock

Edita `app/agents/tools/linix_tools.py` en el diccionario `MOCK_MEMBERS`.

## 🐛 Solución Rápida de Problemas

### Error: OPENAI_API_KEY no configurada
✅ Crea el archivo `.env` con tu API key

### Error: Module not found
✅ Activa el entorno virtual y ejecuta `pip install -r requirements.txt`

### Error: Puerto en uso
✅ Cambia el puerto en `.env` o cierra la aplicación que lo está usando

### WeasyPrint no se instala (Windows)
✅ Es opcional para PDFs. El chatbot genera certificados simulados sin él.

## 📚 Recursos

- **FastAPI Docs:** http://localhost:8000/docs
- **Información del Bot:** http://localhost:8000/api/info
- **Health Check:** http://localhost:8000/health

## 💡 Tips

1. **Desarrollo:** El servidor se recarga automáticamente al cambiar código (gracias a `--reload`)
2. **Logs:** Observa la consola para ver el flujo de ejecución del grafo
3. **Debugging:** Agrega `logger.info()` en cualquier nodo o tool para seguir el flujo
4. **Personalización:** Modifica el `SYSTEM_PROMPT` en `graph.py` para cambiar el comportamiento

## 🎓 Próximos Pasos de Aprendizaje

1. ✅ Ejecuta el chatbot y prueba todas las funcionalidades
2. 📖 Lee el código de `graph.py` para entender el flujo de LangGraph
3. 🔧 Modifica las tools para agregar nuevas funcionalidades
4. 🧪 Experimenta con diferentes prompts en `router_node.py`
5. 🎨 Personaliza la interfaz en `templates/chat.html`

## ✨ ¡Listo!

Tu chatbot Cootradecun está listo para usar. Si tienes dudas, consulta `INSTALL.md` para detalles completos de instalación.

¡Disfruta tu chatbot! 🤖

