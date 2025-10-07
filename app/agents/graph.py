"""
LangGraph - Grafo principal del chatbot Cootradecun
Arquitectura: Router → Tool Calling → Response
"""
import logging
import os
from typing import Annotated, Sequence, Literal
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

# Constantes para START y END en la nueva versión de LangGraph
START = "__start__"
END = "__end__"

# Definir MessagesState manualmente para compatibilidad con LangGraph 0.6+
class MessagesState(TypedDict):
    """Estado del grafo que contiene los mensajes de la conversación"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    route: str  # Ruta determinada por el router

# Importar tools
from .tools.rag_tool import rag_search, initialize_rag
from .tools.linix_tools import get_member_status, simulate_credit, check_credit_eligibility
from .tools.certificate_tool import generate_certificate

# Importar ToolNode después de definir las tools
from langgraph.prebuilt import ToolNode

# Importar nodes
from .nodes.router_node import router_node, route_after_router
from .nodes.respond_node import respond_node

logger = logging.getLogger(__name__)

# 1️⃣ Crear modelo base (OpenAI GPT-4o-mini)
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.warning("⚠️  OPENAI_API_KEY no encontrada en variables de entorno")
    logger.warning("⚠️  El chatbot no funcionará hasta que configures tu API key en el archivo .env")
    # Crear un modelo "dummy" para que el módulo se pueda importar
    llm = None
else:
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=api_key
        )
        logger.info("✅ Modelo OpenAI GPT-4o-mini inicializado")
    except Exception as e:
        logger.error(f"❌ Error inicializando modelo OpenAI: {e}")
        llm = None

# 2️⃣ Registrar herramientas disponibles
tools = [
    rag_search,
    get_member_status,
    simulate_credit,
    check_credit_eligibility,
    generate_certificate
]

# Vincular tools al LLM (solo si llm está disponible)
llm_with_tools = llm.bind_tools(tools) if llm else None

# 3️⃣ System prompt para el chatbot
SYSTEM_PROMPT = """Eres un asistente virtual de Cootradecun, la Cooperativa de Trabajadores de Cundinamarca.

ALCANCE DE TU FUNCIÓN:
Tu ÚNICA función es ayudar a los afiliados con temas relacionados a Cootradecun:
- Consultas sobre servicios y beneficios de la cooperativa
- Horarios de atención y requisitos
- Verificación de estado de afiliación y aportes
- Simulación y solicitud de créditos
- Generación de certificados
- Información sobre aportes, retiros y convenios
- Seguros y protección para afiliados
- Auxilios educativos

RESTRICCIONES IMPORTANTES:
- NO respondas preguntas que NO estén relacionadas con Cootradecun o servicios cooperativos
- NO proporciones información sobre: recetas, deportes, entretenimiento, consejos generales, cultura general, etc.
- Si te preguntan algo fuera del alcance de la cooperativa, responde cortésmente indicando que solo puedes ayudar con temas de Cootradecun

COMPORTAMIENTO:
- Eres amable, profesional y servicial
- Das respuestas claras, concisas y precisas
- Usas las herramientas disponibles cuando sea necesario
- Si no tienes información sobre Cootradecun, lo admites y ofreces alternativas
- No inventes datos personales o financieros
- Pides aclaraciones cuando la consulta es ambigua

RESPUESTAS A PREGUNTAS FUERA DE TEMA:
Si te preguntan algo NO relacionado con Cootradecun, responde:
"Lo siento, soy un asistente especializado en la Cooperativa de Trabajadores de Cundinamarca (Cootradecun). Solo puedo ayudarte con consultas sobre:
- Servicios y beneficios de la cooperativa
- Estado de afiliación y aportes
- Créditos y simulaciones
- Certificados y documentos
- Horarios y requisitos

¿En qué tema relacionado con Cootradecun puedo ayudarte?"

INFORMACIÓN REQUERIDA:
- Para consultas de estado o créditos: número de cédula del afiliado
- Para simulaciones de crédito: monto y plazo deseado

Responde de forma conversacional y útil, pero SIEMPRE dentro del contexto de Cootradecun."""


def call_model_node(state: MessagesState) -> MessagesState:
    """
    Nodo que ejecuta el modelo con capacidad de Tool Calling.
    
    Args:
        state: Estado actual con los mensajes
    
    Returns:
        Dict con los mensajes actualizados (incluyendo posibles tool calls)
    """
    try:
        # Validar que el modelo esté disponible
        if not llm_with_tools:
            logger.error("Modelo no disponible. Verifica tu OPENAI_API_KEY")
            return {
                "messages": [
                    AIMessage(content="⚠️ El chatbot no está configurado correctamente. Por favor, configura tu OPENAI_API_KEY en el archivo .env")
                ]
            }
        
        messages = state.get("messages", [])
        route = state.get("route", "default")
        
        # Agregar system prompt si es el primer mensaje
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        
        logger.info(f"Llamando al modelo (ruta: {route})...")
        
        # Llamar al modelo con tools
        response = llm_with_tools.invoke(messages)
        
        logger.info(f"Respuesta del modelo recibida. Tool calls: {len(response.tool_calls) if hasattr(response, 'tool_calls') else 0}")
        
        return {"messages": [response]}
        
    except Exception as e:
        logger.error(f"Error en call_model_node: {e}")
        return {
            "messages": [
                AIMessage(content=f"Lo siento, ocurrió un error al procesar tu solicitud: {str(e)}")
            ]
        }


def should_continue(state: MessagesState) -> Literal["tools", "respond"]:
    """
    Edge condicional que decide si ejecutar tools o responder directamente.
    
    Returns:
        "tools" si el modelo solicitó tool calls, "respond" si no
    """
    messages = state.get("messages", [])
    if not messages:
        return "respond"
    
    last_message = messages[-1]
    
    # Verificar si hay tool calls pendientes
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.info(f"Tool calls detectados: {len(last_message.tool_calls)}")
        return "tools"
    else:
        logger.info("No hay tool calls, pasando a respond")
        return "respond"


# 4️⃣ Crear checkpointer para memoria persistente
# MemorySaver: guarda en memoria (perfecto para desarrollo y pruebas)
# Para producción, considera usar SqliteSaver o PostgresSaver
memory_checkpointer = MemorySaver()

# 5️⃣ Construcción del grafo
def create_chatbot_graph():
    """
    Crea y compila el grafo del chatbot con memoria persistente.
    
    Returns:
        Grafo compilado listo para ejecutar con checkpointing
    """
    try:
        # Validar que el modelo esté disponible
        if not llm:
            logger.warning("⚠️  Creando grafo sin modelo LLM - configura OPENAI_API_KEY")
        
        # Inicializar RAG
        initialize_rag()
        logger.info("RAG inicializado")
        
        # Crear el grafo
        graph = StateGraph(MessagesState)
        
        # 6️⃣ Agregar nodos
        graph.add_node("router", router_node)
        graph.add_node("call_model", call_model_node)
        graph.add_node("tools", ToolNode(tools=tools))
        graph.add_node("respond", respond_node)
        
        # 7️⃣ Definir transiciones
        # START → router
        graph.add_edge(START, "router")
        
        # router → call_model (basado en la ruta detectada)
        graph.add_conditional_edges(
            "router",
            route_after_router,
            {
                "call_model": "call_model",
                "respond": "respond"
            }
        )
        
        # call_model → tools (si hay tool calls) o respond (si no hay)
        graph.add_conditional_edges(
            "call_model",
            should_continue,
            {
                "tools": "tools",
                "respond": "respond"
            }
        )
        
        # tools → call_model (para que el modelo procese los resultados)
        graph.add_edge("tools", "call_model")
        
        # respond → END
        graph.add_edge("respond", END)
        
        # 8️⃣ Compilar grafo con checkpointer para habilitar memoria
        chatbot_graph = graph.compile(checkpointer=memory_checkpointer)
        
        logger.info("✅ Grafo del chatbot compilado exitosamente con memoria persistente")
        
        return chatbot_graph
        
    except Exception as e:
        logger.error(f"Error creando grafo: {e}")
        raise


# 9️⃣ Función helper para invocar el chatbot con memoria
async def process_message(message: str, session_id: str = "default") -> str:
    """
    Procesa un mensaje del usuario y retorna la respuesta del chatbot.
    Mantiene el contexto de la conversación usando el session_id como thread_id.
    
    Args:
        message: Mensaje del usuario
        session_id: ID de sesión para mantener el contexto de la conversación
    
    Returns:
        Respuesta del chatbot como string
    """
    try:
        # Validar que el grafo esté disponible
        if not chatbot_graph:
            logger.error("Grafo del chatbot no disponible")
            return "⚠️ El chatbot no está configurado correctamente. Por favor, verifica la configuración."
        
        # Preparar el input
        input_state = {
            "messages": [HumanMessage(content=message)]
        }
        
        # Configuración con thread_id para memoria persistente
        config = {
            "configurable": {
                "thread_id": session_id
            }
        }
        
        logger.info(f"[{session_id}] Procesando mensaje: {message[:100]}...")
        
        # Ejecutar el grafo con memoria (config es el segundo argumento)
        result = chatbot_graph.invoke(input_state, config)
        
        # Extraer la respuesta
        messages = result.get("messages", [])
        if messages:
            last_message = messages[-1]
            response = last_message.content if hasattr(last_message, 'content') else str(last_message)
            logger.info(f"[{session_id}] Respuesta generada: {response[:100]}...")
            return response
        else:
            return "Lo siento, no pude generar una respuesta."
            
    except Exception as e:
        logger.error(f"[{session_id}] Error procesando mensaje: {e}")
        return f"Error: {str(e)}"


# Crear instancia global del grafo (se inicializa al importar)
try:
    if llm:
        chatbot_graph = create_chatbot_graph()
        logger.info("✅ Grafo global del chatbot creado correctamente")
    else:
        logger.warning("⚠️  Grafo no creado - falta OPENAI_API_KEY")
        logger.warning("⚠️  Configura tu API key en el archivo .env para usar el chatbot")
        chatbot_graph = None
except Exception as e:
    logger.error(f"❌ Error creando grafo global: {e}")
    chatbot_graph = None

