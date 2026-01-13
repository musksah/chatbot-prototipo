from datetime import datetime
from typing import Annotated, Literal, Optional
from typing_extensions import TypedDict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Track token usage per conversation thread.
_token_totals_by_thread = {}

def _extract_token_usage(result) -> dict:
    if getattr(result, "usage_metadata", None):
        return result.usage_metadata or {}
    response_metadata = getattr(result, "response_metadata", None) or {}
    return response_metadata.get("usage_metadata") or response_metadata.get("usage") or response_metadata.get("token_usage") or {}

def _update_and_log_token_usage(thread_id: str, usage: dict) -> None:
    if not usage:
        return
    prompt_tokens = usage.get("prompt_token_count") or usage.get("prompt_tokens")
    completion_tokens = usage.get("candidates_token_count") or usage.get("completion_tokens")
    total_tokens = usage.get("total_token_count") or usage.get("total_tokens")
    if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
        total_tokens = prompt_tokens + completion_tokens

    logger.info(
        "Gemini tokens for thread=%s: prompt=%s completion=%s total=%s",
        thread_id,
        prompt_tokens,
        completion_tokens,
        total_tokens,
    )

    totals = _token_totals_by_thread.setdefault(
        thread_id,
        {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    )
    if prompt_tokens is not None:
        totals["prompt_tokens"] += prompt_tokens
    if completion_tokens is not None:
        totals["completion_tokens"] += completion_tokens
    if total_tokens is not None:
        totals["total_tokens"] += total_tokens

    logger.info(
        "Gemini token totals for thread=%s: prompt=%s completion=%s total=%s",
        thread_id,
        totals["prompt_tokens"],
        totals["completion_tokens"],
        totals["total_tokens"],
    )

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.messages import ToolMessage

from .tools import (
    ToAtencionAsociado,
    ToNominas,
    ToVivienda,
    ToCertificados,
    CompleteOrEscalate,
    consultar_atencion_asociado,
    consultar_nominas,
    consultar_vivienda,
    solicitar_otp,
    verificar_codigo_otp,
    generar_certificado_tributario,
)

# --- State Definition ---

def update_dialog_stack(left: list[str], right: Optional[str]) -> list[str]:
    """Push or pop the state."""
    if right is None:
        return left
    if right == "pop":
        return left[:-1]
    return left + [right]

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    dialog_state: Annotated[
        list[
            Literal[
                "primary_assistant",
                "atencion_asociado",
                "nominas",
                "vivienda",
                "certificados",
            ]
        ],
        update_dialog_stack,
    ]

# --- Assistant Utility ---

class Assistant:
    def __init__(self, runnable: Runnable, name: str = "Unknown"):
        self.runnable = runnable
        self.name = name

    def __call__(self, state: State, config: RunnableConfig):
        logger.info(f"🤖 Agent '{self.name}' is processing...")
        while True:
            result = self.runnable.invoke(state)
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        
        # Log tool calls if any
        if result.tool_calls:
            for tc in result.tool_calls:
                logger.info(f"🔧 Agent '{self.name}' called tool: {tc['name']} with args: {tc.get('args', {})}")
        else:
            logger.info(f"💬 Agent '{self.name}' responded with content (no tool call)")
        
        thread_id = (config or {}).get("configurable", {}).get("thread_id", "unknown")
        usage = _extract_token_usage(result)
        _update_and_log_token_usage(thread_id, usage)

        return {"messages": result}

def create_entry_node(assistant_name: str, new_dialog_state: str):
    def entry_node(state: State) -> dict:
        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        return {
            "messages": [
                ToolMessage(
                    content=f"The assistant is now the {assistant_name}. Reflect on the above conversation between the host assistant and the user."
                    f" The user's intent is unsatisfied. Use the provided tools to assist the user. Remember, you are {assistant_name},"
                    " and the action is not complete until after you have successfully invoked the appropriate tool."
                    " If the user changes their mind or needs help for other tasks, call the CompleteOrEscalate function to let the primary host assistant take control."
                    " Do not mention who you are - just act as the proxy for the assistant.",
                    tool_call_id=tool_call_id,
                )
            ],
            "dialog_state": new_dialog_state,
        }
    return entry_node

def pop_dialog_state(state: State) -> dict:
    """Pop the dialog stack and return to the main assistant."""
    messages = []
    if state["messages"][-1].tool_calls:
        messages.append(
            ToolMessage(
                content="Resuming dialog with the host assistant. Please reflect on the past conversation and assist the user as needed.",
                tool_call_id=state["messages"][-1].tool_calls[0]["id"],
            )
        )
    return {
        "dialog_state": "pop",
        "messages": messages,
    }

# --- Prompts & Runnables ---

llm = ChatGoogleGenerativeAI(model="gemini-3-pro-preview") # Using Gemini for routing and reasoning

# 1. Primary Assistant
primary_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres el asistente virtual principal de COOTRADECUN (Cooperativa Multiactiva de Trabajadores de la Educación). "
            "Tu objetivo es ser amable, profesional y eficiente.\n\n"
            "**REGLA DE CLARIFICACIÓN** (IMPORTANTE):\n"
            "Si la pregunta del usuario es ambigua, incompleta o no está claro a qué área pertenece:\n"
            "- HAZ PREGUNTAS DE SEGUIMIENTO para entender mejor qué necesita.\n"
            "- Ejemplos de preguntas clarificadoras:\n"
            "  • '¿Te refieres a información sobre proyectos de vivienda o sobre créditos?'\n"
            "  • '¿Necesitas ayuda con trámites de asociación o con pagos?'\n"
            "  • '¿Podrías darme más detalles sobre lo que necesitas?'\n"
            "- NO delegues ni respondas hasta tener claridad sobre la intención del usuario.\n\n"
            "**REGLA DE DELEGACIÓN** (una vez clara la intención):\n"
            "TÚ NO TIENES acceso a información detallada. Cuando tengas claridad, delega:\n"
            "- VIVIENDA (proyectos, precios, créditos hipotecarios, Pedregal, Rancho Grande) → USA ToVivienda\n"
            "- NÓMINAS (desprendibles, pagos, libranzas) → USA ToNominas\n"
            "- ASOCIACIÓN (requisitos, auxilios, convenios) → USA ToAtencionAsociado\n"
            "- CERTIFICADOS (certificado tributario, certificado de aportes, paz y salvo) → USA ToCertificados\n\n"
            "**REGLA DE TEMAS NO RELACIONADOS**:\n"
            "Si el usuario pregunta sobre temas NO relacionados con COOTRADECUN (recetas, clima, deportes, etc.), "
            "responde: 'Lo siento, solo puedo ayudarte con temas relacionados con COOTRADECUN.'\n\n"
            "Tus tareas directas:\n"
            "1. Saludar cordialmente.\n"
            "2. Hacer preguntas clarificadoras si hay ambigüedad.\n"
            "3. Responder preguntas MUY generales ('¿Qué es Cootradecun?').\n"
            "4. DELEGAR cuando tengas certeza de la intención del usuario.\n"
            "\nCurrent time: {time}."
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

primary_tools = [ToAtencionAsociado, ToNominas, ToVivienda, ToCertificados]
primary_runnable = primary_prompt | llm.bind_tools(primary_tools)

# 2. Atencion Asociado Agent
asociado_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres el experto en Atención al Asociado de COOTRADECUN.\n\n"
            "**REGLA CRÍTICA - OBLIGATORIA**:\n"
            "1. SIEMPRE debes usar la herramienta `consultar_atencion_asociado` ANTES de responder CUALQUIER pregunta.\n"
            "2. Incluso para preguntas de seguimiento, DEBES consultar la herramienta.\n"
            "3. NUNCA respondas de memoria o con información que no provenga de la herramienta.\n"
            "4. NUNCA digas 'no tengo información' sin PRIMERO haber consultado la herramienta.\n\n"
            "Áreas de especialidad:\n"
            "- Requisitos de asociación y documentos necesarios.\n"
            "- Auxilios: solidaridad, discapacidad, incapacidad, estudios.\n"
            "- Convenios: parques, educación, salud, exequiales.\n\n"
            "Si el usuario cambia de tema a vivienda o pagos, usa CompleteOrEscalate.\n"
            "\nCurrent time: {time}."
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

asociado_tools = [consultar_atencion_asociado, CompleteOrEscalate]
asociado_runnable = asociado_prompt | llm.bind_tools(asociado_tools)

# 3. Nominas Agent
nominas_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres el experto en Nóminas y Tesorería de COOTRADECUN.\n\n"
            "**REGLA CRÍTICA - OBLIGATORIA**:\n"
            "1. SIEMPRE debes usar la herramienta `consultar_nominas` ANTES de responder CUALQUIER pregunta.\n"
            "2. Incluso para preguntas de seguimiento, DEBES consultar la herramienta.\n"
            "3. NUNCA respondas de memoria o con información que no provenga de la herramienta.\n"
            "4. NUNCA digas 'no tengo información' sin PRIMERO haber consultado la herramienta.\n\n"
            "Áreas de especialidad:\n"
            "- Desprendibles de pago.\n"
            "- Medios de pago: PSE, Baloto (código 3898), Banco de Bogotá.\n"
            "- Libranzas y deducciones.\n\n"
            "Para saldos específicos, recuerda que el usuario debe ingresar al Portal Transaccional.\n"
            "Si el usuario cambia de tema, usa CompleteOrEscalate.\n"
            "\nCurrent time: {time}."
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

nominas_tools = [consultar_nominas, CompleteOrEscalate]
nominas_runnable = nominas_prompt | llm.bind_tools(nominas_tools)

# 4. Vivienda Agent
vivienda_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres el asesor experto en Vivienda de COOTRADECUN. Tu objetivo es ayudar a los asociados a cumplir el sueño de tener vivienda propia.\n\n"
            "**REGLA CRÍTICA - OBLIGATORIA**: \n"
            "1. SIEMPRE debes usar la herramienta `consultar_vivienda` ANTES de responder CUALQUIER pregunta.\n"
            "2. Incluso para preguntas cortas de seguimiento como '¿Cuál es el precio?' o '¿Dónde queda?', DEBES usar la herramienta.\n"
            "3. Si el usuario preguntó previamente sobre un proyecto específico (ej: Pedregal), usa ese contexto en tu query a la herramienta.\n"
            "4. NUNCA digas 'no tengo información' o 'contacta al equipo' sin PRIMERO haber consultado la herramienta.\n\n"
            "Ejemplos de queries para la herramienta:\n"
            "- Si preguntan 'cuál es el precio' después de hablar de Pedregal → consultar_vivienda('precio Pedregal')\n"
            "- Si preguntan '¿dónde queda?' → consultar_vivienda('ubicación [nombre del proyecto mencionado]')\n\n"
            "Áreas de especialidad:\n"
            "- Proyectos: 'Rancho Grande' (Melgar), 'El Pedregal' (Fusagasugá) y 'Arayanes de Peñalisa'.\n"
            "- Crédito: Montos, plazos y tasas preferenciales.\n"
            "- Simulación: Simulador de crédito en la web.\n\n"
            "Si el usuario cambia de tema a algo no relacionado con vivienda, usa CompleteOrEscalate.\n"
            "\nCurrent time: {time}."
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

vivienda_tools = [consultar_vivienda, CompleteOrEscalate]
vivienda_runnable = vivienda_prompt | llm.bind_tools(vivienda_tools)

# 5. Certificados Agent (with OTP authentication)
certificados_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres el especialista en Certificados de COOTRADECUN. Tu trabajo es generar certificados oficiales "
            "para los asociados, PERO SOLO después de verificar su identidad mediante OTP.\n\n"
            "**FLUJO OBLIGATORIO para generar certificados:**\n"
            "1. PRIMERO: Solicita al usuario su número de cédula y teléfono.\n"
            "2. SEGUNDO: Usa la herramienta `solicitar_otp` con la cédula y teléfono.\n"
            "3. TERCERO: Pide al usuario que ingrese el código de 6 dígitos que recibió por WhatsApp.\n"
            "4. CUARTO: Usa la herramienta `verificar_codigo_otp` con la cédula y el código.\n"
            "5. QUINTO: Si la verificación es exitosa, usa `generar_certificado_tributario`.\n\n"
            "**IMPORTANTE:**\n"
            "- NUNCA generes un certificado sin verificar el OTP primero.\n"
            "- Si el usuario proporciona un código incorrecto, permítele intentar de nuevo.\n"
            "- El número de teléfono debe ser colombiano (puede ser con o sin +57).\n\n"
            "**Tipos de certificados disponibles:**\n"
            "- Certificado Tributario (para declaración de renta)\n"
            "- Certificado de Aportes\n"
            "- Certificado de Paz y Salvo\n\n"
            "Si el usuario cambia de tema, usa CompleteOrEscalate.\n"
            "\nCurrent time: {time}."
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

certificados_tools = [solicitar_otp, verificar_codigo_otp, generar_certificado_tributario, CompleteOrEscalate]
certificados_runnable = certificados_prompt | llm.bind_tools(certificados_tools)


# --- Graph Construction ---

builder = StateGraph(State)

# Primary Assistant Node
builder.add_node("primary_assistant", Assistant(primary_runnable, name="Primary Assistant"))
builder.add_edge(START, "primary_assistant")

# --- Specialized Workflows ---

def create_workflow(name: str, runnable: Runnable, tools: list, entry_state: str):
    # Entry Node
    builder.add_node(f"enter_{name}", create_entry_node(f"{name.capitalize()} Assistant", entry_state))
    
    # Agent Node
    builder.add_node(name, Assistant(runnable, name=f"{name.capitalize()} Agent"))
    builder.add_edge(f"enter_{name}", name)
    
    # Tools Node - ONLY include callable tools, not Pydantic schemas like CompleteOrEscalate
    callable_tools = [t for t in tools if callable(getattr(t, 'invoke', None)) or hasattr(t, 'func')]
    tool_node = ToolNode(callable_tools)
    builder.add_node(f"{name}_tools", tool_node)
    
    # Edge Logic
    def route_workflow(state: State):
        route = tools_condition(state)
        if route == END:
            return END
        tool_calls = state["messages"][-1].tool_calls
        did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
        if did_cancel:
            return "leave_skill"
        return f"{name}_tools"

    builder.add_conditional_edges(
        name,
        route_workflow,
        [f"{name}_tools", "leave_skill", END]
    )
    builder.add_edge(f"{name}_tools", name)

# Leave Skill (Shared)
builder.add_node("leave_skill", pop_dialog_state)
builder.add_edge("leave_skill", "primary_assistant")

# Create Sub-graphs
create_workflow("atencion_asociado", asociado_runnable, asociado_tools, "atencion_asociado")
create_workflow("nominas", nominas_runnable, nominas_tools, "nominas")
create_workflow("vivienda", vivienda_runnable, vivienda_tools, "vivienda")
create_workflow("certificados", certificados_runnable, certificados_tools, "certificados")

# Primary Routing Logic
def route_primary(state: State):
    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        if tool_calls[0]["name"] == ToAtencionAsociado.__name__:
            return "enter_atencion_asociado"
        elif tool_calls[0]["name"] == ToNominas.__name__:
            return "enter_nominas"
        elif tool_calls[0]["name"] == ToVivienda.__name__:
            return "enter_vivienda"
        elif tool_calls[0]["name"] == ToCertificados.__name__:
            return "enter_certificados"
    return END

builder.add_conditional_edges(
    "primary_assistant",
    route_primary,
    ["enter_atencion_asociado", "enter_nominas", "enter_vivienda", "enter_certificados", END]
)

graph = builder.compile()
