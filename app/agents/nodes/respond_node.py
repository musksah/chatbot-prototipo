"""
Respond Node - Formatea y prepara la respuesta final para el usuario
"""
from langchain_core.messages import AIMessage
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def respond_node(state: Dict[str, Any]) -> dict:
    """
    Formatea la salida final del chatbot basándose en los mensajes del estado.
    
    Args:
        state: Estado actual del grafo con los mensajes
    
    Returns:
        Dict con los mensajes actualizados
    """
    try:
        messages = state.get("messages", [])
        
        if not messages:
            logger.warning("respond_node: No hay mensajes en el estado")
            return {
                "messages": [
                    AIMessage(content="🤖 Lo siento, no pude procesar tu solicitud. ¿Podrías reformular tu pregunta?")
                ]
            }
        
        # El último mensaje debería ser la respuesta del LLM o de las tools
        last_message = messages[-1]
        
        # Si ya es un mensaje formateado, devolverlo tal cual
        if isinstance(last_message, AIMessage):
            logger.info(f"Respuesta final: {last_message.content[:100]}...")
            return {"messages": messages}
        
        # Si no, crear un mensaje de AI con el contenido
        response_content = str(last_message)
        
        # Agregar emoji de bot si no está presente
        if not response_content.startswith("🤖"):
            response_content = f"🤖 {response_content}"
        
        logger.info(f"Respuesta formateada: {response_content[:100]}...")
        
        return {
            "messages": [AIMessage(content=response_content)]
        }
        
    except Exception as e:
        logger.error(f"Error en respond_node: {e}")
        return {
            "messages": [
                AIMessage(content="🤖 Ocurrió un error al procesar tu solicitud. Por favor, intenta de nuevo.")
            ]
        }


def format_tool_response(tool_name: str, tool_output: dict) -> str:
    """
    Formatea la salida de una tool para que sea más amigable.
    
    Args:
        tool_name: Nombre de la tool ejecutada
        tool_output: Salida de la tool
    
    Returns:
        String formateado para mostrar al usuario
    """
    try:
        if tool_name == "rag_search":
            if tool_output.get("found"):
                return f"📚 {tool_output.get('answer', 'Sin respuesta')}"
            else:
                return "📚 No encontré información específica sobre tu consulta."
        
        elif tool_name == "get_member_status":
            if tool_output.get("found"):
                data = tool_output.get("data", {})
                return f"""
👤 **Estado de Afiliación**

**Nombre:** {data.get('nombre')}
**Cédula:** {data.get('cedula')}
**Estado:** {data.get('estado', '').upper()}
**Fecha de afiliación:** {data.get('fecha_afiliacion')}
**Aportes:** {data.get('estado_aportes')}
**Saldo aportes:** {data.get('saldo_aportes')}
**Último aporte:** {data.get('ultimo_aporte')}
**Créditos activos:** {data.get('creditos_activos')}
**Cupo disponible:** {data.get('cupo_disponible')}
                """.strip()
            else:
                return tool_output.get("message", "No se encontró información del afiliado.")
        
        elif tool_name == "simulate_credit":
            if tool_output.get("success"):
                sim = tool_output.get("simulacion", {})
                return f"""
💰 **Simulación de Crédito**

**Monto solicitado:** {sim.get('monto_solicitado')}
**Plazo:** {sim.get('plazo_meses')} meses
**Tasa anual:** {sim.get('tasa_anual')}
**Cuota mensual:** {sim.get('cuota_mensual')}
**Total a pagar:** {sim.get('total_pagar')}
**Total intereses:** {sim.get('total_intereses')}

*{tool_output.get('nota', '')}*
                """.strip()
            else:
                return f"❌ {tool_output.get('message', 'Error en la simulación')}"
        
        elif tool_name == "generate_certificate":
            if tool_output.get("success"):
                cert = tool_output.get("certificate", {})
                return f"""
📄 **Certificado Generado**

**Afiliado:** {cert.get('afiliado')}
**Tipo:** {cert.get('tipo')}
**Fecha:** {cert.get('fecha_generacion')}
**Código:** {cert.get('codigo')}

{tool_output.get('message', '')}
                """.strip()
            else:
                return f"❌ {tool_output.get('message', 'Error al generar certificado')}"
        
        else:
            # Formato genérico
            return str(tool_output.get("message", tool_output))
            
    except Exception as e:
        logger.error(f"Error formateando respuesta de {tool_name}: {e}")
        return str(tool_output)

