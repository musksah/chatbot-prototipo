"""
FastAPI Main Application - Chatbot Cootradecun
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
try:
    load_dotenv()
except UnicodeDecodeError:
    # Si hay error de codificación, intentar recrear el archivo .env
    print("⚠️  Advertencia: Archivo .env con codificación incorrecta")
    print("Se recomienda recrear el archivo .env con codificación UTF-8")
except Exception as e:
    print(f"⚠️  Advertencia al cargar .env: {e}")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar routers
from app.routers import chat

# Crear aplicación FastAPI
app = FastAPI(
    title="Chatbot Cootradecun",
    description="Prototipo MVP del chatbot para la Cooperativa de Trabajadores de Cundinamarca",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar directorios estáticos y templates
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Incluir routers
app.include_router(chat.router, prefix="/api", tags=["chat"])


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Página principal - Interfaz del chatbot
    """
    return templates.TemplateResponse("chat.html", {"request": request})


@app.get("/health")
async def health_check():
    """
    Endpoint de salud para verificar que el servicio está funcionando
    """
    return {
        "status": "healthy",
        "service": "Chatbot Cootradecun",
        "version": "1.0.0"
    }


@app.get("/api/info")
async def get_info():
    """
    Información sobre el chatbot y sus capacidades
    """
    return {
        "name": "Chatbot Cootradecun",
        "version": "1.1.0",
        "description": "Asistente virtual para la Cooperativa de Trabajadores de Cundinamarca",
        "capabilities": [
            "Consultas sobre horarios y servicios",
            "Verificación de estado de afiliación",
            "Simulación de créditos",
            "Generación de certificados",
            "Respuestas a preguntas frecuentes",
            "Memoria persistente de conversaciones por sesión"
        ],
        "tools": [
            "rag_search - Búsqueda en base de conocimiento",
            "get_member_status - Consulta estado de afiliado",
            "simulate_credit - Simulación de créditos",
            "check_credit_eligibility - Verificación de elegibilidad",
            "generate_certificate - Generación de certificados PDF"
        ],
        "features": {
            "memory": {
                "enabled": True,
                "type": "MemorySaver (in-memory)",
                "description": "Mantiene el contexto de conversación por session_id",
                "persistence": "En memoria (se pierde al reiniciar el servidor)"
            },
            "multi_session": {
                "enabled": True,
                "description": "Soporta múltiples conversaciones simultáneas con diferentes session_id"
            },
            "context_restrictions": {
                "enabled": True,
                "description": "El bot solo responde preguntas relacionadas con Cootradecun",
                "scope": "Servicios cooperativos, créditos, afiliación, certificados",
                "rejects": "Preguntas fuera de contexto (recetas, deportes, etc.)"
            }
        }
    }


@app.on_event("startup")
async def startup_event():
    """
    Eventos al iniciar la aplicación
    """
    logger.info("=" * 60)
    logger.info("🚀 Iniciando Chatbot Cootradecun")
    logger.info("=" * 60)
    
    # Verificar OPENAI_API_KEY
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("⚠️  OPENAI_API_KEY no configurada")
    else:
        logger.info("✅ OPENAI_API_KEY configurada")
    
    # Crear directorios necesarios
    data_dir = BASE_DIR / "data" / "generated"
    data_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"✅ Directorio de datos: {data_dir}")
    
    logger.info("✅ Aplicación lista")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Eventos al cerrar la aplicación
    """
    logger.info("🛑 Cerrando Chatbot Cootradecun")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Iniciando servidor en http://{host}:{port}")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

