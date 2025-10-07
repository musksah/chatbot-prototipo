"""
Router Node - Clasifica la intención del usuario y determina el flujo
"""
from typing import Literal, Dict, Any
import logging

logger = logging.getLogger(__name__)


def router_node(state: Dict[str, Any]) -> dict:
    """
    Analiza el mensaje del usuario y decide qué ruta tomar en el grafo.
    
    Returns:
        Dict con la ruta a seguir ("route")
    """
    try:
        # Obtener el último mensaje del usuario
        messages = state.get("messages", [])
        if not messages:
            logger.warning("No hay mensajes en el estado")
            return {"route": "default"}
        
        # Tomar el último mensaje
        last_message = messages[-1]
        text = last_message.content.lower() if hasattr(last_message, 'content') else str(last_message).lower()
        
        logger.info(f"Router analizando: {text[:100]}...")
        
        # Clasificación por palabras clave
        # 1. Certificados
        if any(word in text for word in ["certificado", "certificación", "afiliación", "constancia"]):
            logger.info("Ruta: certificate")
            return {"route": "certificate"}
        
        # 2. Consultas Linix (estado, aportes, créditos)
        elif any(word in text for word in ["estado", "aportes", "saldo", "cuota", "crédito", "prestamo", "préstamo"]):
            logger.info("Ruta: linix")
            return {"route": "linix"}
        
        # 3. Simulación de créditos
        elif any(word in text for word in ["simular", "simulación", "calcular", "cuanto pagar", "cuánto pagar"]):
            logger.info("Ruta: linix")
            return {"route": "linix"}
        
        # 4. FAQ (horarios, beneficios, información general)
        elif any(word in text for word in ["horario", "beneficio", "servicio", "requisito", "cómo", "como", "qué", "que"]):
            logger.info("Ruta: faq")
            return {"route": "faq"}
        
        # 5. Saludos y conversación general
        elif any(word in text for word in ["hola", "buenos", "buenas", "gracias", "ayuda", "ayudar"]):
            logger.info("Ruta: faq")
            return {"route": "faq"}
        
        # Default: intentar con FAQ
        else:
            logger.info("Ruta: default (FAQ)")
            return {"route": "faq"}
            
    except Exception as e:
        logger.error(f"Error en router_node: {e}")
        return {"route": "default"}


def route_after_router(state: Dict[str, Any]) -> Literal["call_model", "respond"]:
    """
    Edge condicional que decide si llamar al modelo o responder directamente.
    
    Returns:
        "call_model" para procesar con LLM y tools, "respond" para respuesta directa
    """
    route = state.get("route", "default")
    
    if route in ["faq", "linix", "certificate"]:
        return "call_model"
    else:
        return "respond"

