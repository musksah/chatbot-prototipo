# Guía de Instalación - Chatbot Cootradecun

## 📋 Requisitos Previos

- Python 3.11 o superior
- pip (gestor de paquetes de Python)
- Una API key de OpenAI (GPT-4o-mini)

## 🔧 Instalación Paso a Paso

### 1. Clonar o descargar el proyecto

```bash
cd mvp-chatbot-cootradecun
```

### 2. Crear entorno virtual

**En Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate
```

**En Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**En Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

Si encuentras errores con WeasyPrint en Windows, puedes omitirlo temporalmente:
```bash
pip install -r requirements.txt --no-deps
pip install fastapi uvicorn langchain langchain-openai langgraph chromadb python-dotenv pydantic requests jinja2
```

### 4. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Edita el archivo `.env` y agrega tu API key de OpenAI:

```
OPENAI_API_KEY=sk-tu-api-key-aqui
ENVIRONMENT=development
```

### 5. Verificar la instalación

```bash
python test_chatbot.py
```

Si todo está bien, deberías ver las pruebas ejecutándose correctamente.

## ▶️ Ejecutar la aplicación

### Opción 1: Usando el script de inicio

```bash
python run.py
```

### Opción 2: Usando uvicorn directamente

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Opción 3: Desde el módulo principal

```bash
python -m app.main
```

## 🌐 Acceder a la aplicación

Una vez iniciado el servidor:

- **Interfaz web del chatbot:** http://localhost:8000
- **Documentación de la API:** http://localhost:8000/docs
- **Health check:** http://localhost:8000/health
- **Info del chatbot:** http://localhost:8000/api/info

## 🧪 Probar la API directamente

### Usando curl (Windows PowerShell):

```powershell
$body = @{
    message = "¿Cuáles son los horarios de atención?"
    session_id = "test_session"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/chat" -Method POST -Body $body -ContentType "application/json"
```

### Usando curl (Linux/Mac):

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "¿Cuáles son los horarios de atención?",
    "session_id": "test_session"
  }'
```

### Usando Python requests:

```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "message": "¿Cuáles son los horarios de atención?",
        "session_id": "test_session"
    }
)

print(response.json())
```

## 🔍 Solución de Problemas

### Error: OPENAI_API_KEY no configurada

**Solución:** Asegúrate de tener el archivo `.env` con tu API key válida.

### Error: Module not found

**Solución:** Verifica que el entorno virtual esté activado y las dependencias instaladas:
```bash
pip list
```

### Error: WeasyPrint installation failed (Windows)

**Solución:** WeasyPrint es opcional para generar PDFs. El chatbot funcionará con certificados simulados si no está instalado. Para instalarlo en Windows, necesitas GTK3:

1. Descarga GTK3: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
2. Instala GTK3
3. Reinstala WeasyPrint: `pip install weasyprint`

### Error: ChromaDB issues

**Solución:** ChromaDB se inicializa automáticamente en memoria. Si tienes problemas:
```bash
pip uninstall chromadb
pip install chromadb==0.4.22
```

### Puerto 8000 ya en uso

**Solución:** Cambia el puerto en el archivo `.env` o al ejecutar:
```bash
uvicorn app.main:app --reload --port 8001
```

## 📦 Dependencias Principales

- **FastAPI** - Framework web
- **LangChain** - Orquestación de LLMs
- **LangGraph** - Construcción de grafos de agentes
- **OpenAI** - API de GPT-4o-mini
- **ChromaDB** - Base de datos vectorial
- **WeasyPrint** - Generación de PDFs (opcional)

## 🔐 Seguridad

- Nunca subas tu archivo `.env` a control de versiones
- Mantén tu API key de OpenAI privada
- En producción, usa variables de entorno del sistema
- Considera implementar rate limiting y autenticación

## 📚 Próximos Pasos

1. Explora la documentación de la API en `/docs`
2. Prueba diferentes consultas en la interfaz web
3. Revisa los logs para entender el flujo de ejecución
4. Personaliza las herramientas según tus necesidades

## 🆘 Soporte

Si encuentras problemas, revisa:
- Los logs de la consola
- La documentación de FastAPI: https://fastapi.tiangolo.com
- La documentación de LangGraph: https://langchain-ai.github.io/langgraph/

