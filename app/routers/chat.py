"""
Chat Router - Endpoints para interacción con el chatbot
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from app.agents.graph import chatbot_graph
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    """Modelo de solicitud para el chat"""
    message: str = Field(..., description="Mensaje del usuario", min_length=1)
    session_id: Optional[str] = Field(default="default", description="ID de sesión")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "¿Cuáles son los horarios de atención?",
                "session_id": "user_123"
            }
        }


class ChatResponse(BaseModel):
    """Modelo de respuesta del chat"""
    response: str = Field(..., description="Respuesta del chatbot")
    session_id: str = Field(..., description="ID de sesión")
    timestamp: str = Field(..., description="Timestamp de la respuesta")
    processing_time: Optional[float] = Field(None, description="Tiempo de procesamiento en segundos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "🤖 Cootradecun atiende de lunes a viernes de 8:00 AM a 5:00 PM...",
                "session_id": "user_123",
                "timestamp": "2024-10-04T12:00:00",
                "processing_time": 1.23
            }
        }


class ErrorResponse(BaseModel):
    """Modelo de respuesta de error"""
    error: str
    detail: Optional[str] = None
    timestamp: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint principal del chat - Procesa un mensaje y devuelve la respuesta.
    Mantiene el contexto de la conversación usando el session_id.
    
    Args:
        request: Objeto ChatRequest con el mensaje del usuario y session_id
    
    Returns:
        ChatResponse con la respuesta del chatbot
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"[{request.session_id}] Mensaje recibido: {request.message[:100]}")
        
        # Validar que el grafo esté disponible
        if chatbot_graph is None:
            logger.error("Chatbot graph no está inicializado")
            raise HTTPException(
                status_code=503,
                detail="El chatbot no está disponible. Por favor, verifica la configuración."
            )
        
        # Preparar el input para el grafo
        input_state = {
            "messages": [HumanMessage(content=request.message)]
        }
        
        # Configuración con thread_id para memoria persistente
        config = {
            "configurable": {
                "thread_id": request.session_id
            }
        }
        
        # Ejecutar el grafo con memoria (config como segundo argumento)
        result = chatbot_graph.invoke(input_state, config)
        
        # Extraer la respuesta
        messages = result.get("messages", [])
        if messages:
            last_message = messages[-1]
            response_text = last_message.content if hasattr(last_message, 'content') else str(last_message)
        else:
            response_text = "Lo siento, no pude generar una respuesta."
        
        # Calcular tiempo de procesamiento
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        logger.info(f"[{request.session_id}] Respuesta generada en {processing_time:.2f}s")
        
        return ChatResponse(
            response=response_text,
            session_id=request.session_id,
            timestamp=end_time.isoformat(),
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request.session_id}] Error procesando mensaje: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar el mensaje: {str(e)}"
        )


@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    Obtiene el historial de chat de una sesión desde el checkpointer.
    
    Args:
        session_id: ID de la sesión
    
    Returns:
        Lista de mensajes de la sesión
    """
    try:
        logger.info(f"Consultando historial para sesión: {session_id}")
        
        # Validar que el grafo esté disponible
        if chatbot_graph is None:
            raise HTTPException(
                status_code=503,
                detail="El chatbot no está disponible."
            )
        
        # Configuración con thread_id
        config = {
            "configurable": {
                "thread_id": session_id
            }
        }
        
        # Obtener el estado guardado de la sesión
        try:
            state = chatbot_graph.get_state(config)
            messages = state.values.get("messages", [])
            
            # Convertir mensajes a formato serializable
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "type": msg.__class__.__name__,
                    "content": msg.content if hasattr(msg, 'content') else str(msg),
                    "role": getattr(msg, 'type', 'unknown')
                })
            
            return {
                "session_id": session_id,
                "message_count": len(formatted_messages),
                "messages": formatted_messages,
                "has_state": len(messages) > 0
            }
            
        except Exception as e:
            # Si no hay estado guardado para esta sesión
            logger.info(f"No hay historial para sesión {session_id}: {e}")
            return {
                "session_id": session_id,
                "message_count": 0,
                "messages": [],
                "has_state": False,
                "note": "No hay conversaciones previas en esta sesión"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo historial: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener historial: {str(e)}"
        )


@router.delete("/chat/history/{session_id}")
async def clear_chat_history(session_id: str):
    """
    Limpia el historial de chat de una sesión específica.
    Elimina todos los mensajes y el estado guardado.
    
    Args:
        session_id: ID de la sesión
    
    Returns:
        Confirmación de limpieza
    """
    try:
        logger.info(f"Limpiando historial para sesión: {session_id}")
        
        # Validar que el grafo esté disponible
        if chatbot_graph is None:
            raise HTTPException(
                status_code=503,
                detail="El chatbot no está disponible."
            )
        
        # Configuración con thread_id
        config = {
            "configurable": {
                "thread_id": session_id
            }
        }
        
        try:
            # Verificar si existe estado para esta sesión
            state = chatbot_graph.get_state(config)
            messages_count = len(state.values.get("messages", []))
            
            # Limpiar el estado - actualizar con mensajes vacíos
            # Nota: MemorySaver no tiene método delete directo, 
            # así que actualizamos con estado vacío
            chatbot_graph.update_state(config, {"messages": []})
            
            logger.info(f"✅ Historial limpiado para sesión {session_id} ({messages_count} mensajes)")
            
            return {
                "success": True,
                "session_id": session_id,
                "messages_deleted": messages_count,
                "message": f"Historial limpiado exitosamente ({messages_count} mensajes eliminados)"
            }
            
        except Exception as e:
            # Si no hay estado, está bien, no hay nada que limpiar
            logger.info(f"No había historial para limpiar en sesión {session_id}")
            return {
                "success": True,
                "session_id": session_id,
                "messages_deleted": 0,
                "message": "No había historial previo para esta sesión"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error limpiando historial: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al limpiar historial: {str(e)}"
        )


@router.get("/chat/sessions")
async def list_active_sessions():
    """
    Lista todas las sesiones con historial guardado.
    
    Returns:
        Lista de sesiones activas con información básica
    """
    try:
        logger.info("Listando sesiones activas")
        
        # Validar que el grafo esté disponible
        if chatbot_graph is None:
            raise HTTPException(
                status_code=503,
                detail="El chatbot no está disponible."
            )
        
        # Nota: MemorySaver no expone directamente todas las sesiones
        # Esta es una limitación del checkpointer en memoria
        # Para producción con SQLite/Postgres se puede consultar la DB
        
        return {
            "note": "Listado de sesiones no disponible con MemorySaver in-memory",
            "recommendation": "Para listar sesiones, considera usar SqliteSaver o PostgresSaver",
            "memory_type": "in-memory",
            "tip": "Puedes consultar una sesión específica usando GET /api/chat/history/{session_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listando sesiones: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar sesiones: {str(e)}"
        )


@router.get("/chat/tools")
async def get_available_tools():
    """
    Obtiene la lista de herramientas (tools) disponibles
    
    Returns:
        Lista de tools con sus descripciones
    """
    return {
        "tools": [
            {
                "name": "rag_search",
                "description": "Busca información en la base de conocimiento de Cootradecun",
                "parameters": ["query", "top_k"]
            },
            {
                "name": "get_member_status",
                "description": "Consulta el estado de afiliación y aportes de un asociado",
                "parameters": ["cedula"]
            },
            {
                "name": "simulate_credit",
                "description": "Simula un crédito calculando cuota mensual y total a pagar",
                "parameters": ["monto", "plazo_meses", "tasa_anual"]
            },
            {
                "name": "check_credit_eligibility",
                "description": "Verifica si un afiliado es elegible para un crédito",
                "parameters": ["cedula", "monto_solicitado"]
            },
            {
                "name": "generate_certificate",
                "description": "Genera un certificado PDF para un afiliado",
                "parameters": ["cedula", "tipo"]
            }
        ],
        "memory_enabled": True,
        "checkpointer_type": "MemorySaver (in-memory)"
    }


@router.post("/chat/test")
async def test_chatbot():
    """
    Endpoint de prueba para verificar que el chatbot funciona
    
    Returns:
        Respuesta de prueba del chatbot
    """
    try:
        test_message = "Hola, ¿cuáles son los horarios de atención?"
        
        request = ChatRequest(
            message=test_message,
            session_id="test"
        )
        
        response = await chat(request)
        
        return {
            "success": True,
            "test_message": test_message,
            "response": response.dict()
        }
        
    except Exception as e:
        logger.error(f"Error en test: {e}")
        return {
            "success": False,
            "error": str(e)
        }

