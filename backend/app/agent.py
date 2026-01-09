from datetime import datetime
from typing import Annotated, Literal, Optional
from typing_extensions import TypedDict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.messages import ToolMessage

from .tools import (
    ToAtencionAsociado,
    ToNominas,
    ToVivienda,
    CompleteOrEscalate,
    consultar_atencion_asociado,
    consultar_nominas,
    consultar_vivienda,
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

llm = ChatOpenAI(model="gpt-4o") # Using a strong model for routing and reasoning

# 1. Primary Assistant
primary_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres el asistente virtual principal de COOTRADECUN (Cooperativa Multiactiva de Trabajadores de la Educación). "
            "Tu objetivo es ser amable, profesional y eficiente.\n\n"
            "**REGLA IMPORTANTE**: SOLO puedes responder preguntas relacionadas con COOTRADECUN y sus servicios. "
            "Si el usuario pregunta sobre temas NO relacionados (recetas, clima, deportes, tecnología, etc.), "
            "debes responder amablemente: 'Lo siento, solo puedo ayudarte con temas relacionados con COOTRADECUN. "
            "¿Hay algo sobre nuestros servicios de asociación, nóminas o vivienda en lo que pueda asistirte?'\n\n"
            "Tus tareas son:\n"
            "1. Saludar cordialmente al asociado y preguntar en qué puedes ayudarle.\n"
            "2. Analizar la consulta del usuario para determinar a qué departamento corresponde.\n"
            "3. Utilizar las herramientas de transferencia (ToAtencionAsociado, ToNominas, ToVivienda) para delegar la conversación al experto adecuado.\n"
            "Si la duda es general sobre COOTRADECUN (ej. '¿Qué es Cootradecun?'), respóndela tú mismo.\n\n"
            "Departamentos de delegación:\n"
            "- Atención al Asociado: Para trámites de asociación, auxilios (solidaridad, educación), convenios recreativos y PQRS.\n"
            "- Nóminas: Para descarga de desprendibles, canales de pago (PSE, Baloto), libranzas y estados de cuenta.\n"
            "- Vivienda: Para créditos hipotecarios, proyectos de vivienda (ej. Rancho Grande, El Pedregal) y simuladores de crédito de vivienda.\n"
            "\nCurrent time: {time}."
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

primary_tools = [ToAtencionAsociado, ToNominas, ToVivienda]
primary_runnable = primary_prompt | llm.bind_tools(primary_tools)

# 2. Atencion Asociado Agent
asociado_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres el experto en Atención al Asociado de COOTRADECUN. Tienes un conocimiento profundo sobre los beneficios de ser parte de la cooperativa.\n"
            "Áreas de especialidad:\n"
            "- Requisitos: Quiénes se pueden asociar y documentos necesarios.\n"
            "- Auxilios: Detalles sobre auxilios de solidaridad, discapacidad, incapacidad y estudios.\n"
            "- Convenios: Alianzas con parques (Ikarus), educación, salud y servicios exequiales.\n"
            "Reglas de comportamiento:\n"
            "- Responde siempre basándote en las políticas oficiales de la cooperativa (usa la herramienta consultar_atencion_asociado).\n"
            "- Si el usuario cambia de tema a temas de vivienda o pagos, utiliza la función CompleteOrEscalate para devolver el control al Asistente Primario.\n"
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
            "Eres el experto en el departamento de Nóminas y Tesorería de COOTRADECUN. Tu tono es preciso y orientado al servicio financiero.\n"
            "Áreas de especialidad:\n"
            "- Desprendibles: Guía para la descarga de desprendibles de pago desde el portal transaccional.\n"
            "- Medios de Pago: Información sobre pagos vía PSE, convenios con Baloto (código 3898), Banco de Bogotá y transferencias.\n"
            "- Deducciones: Explicación sobre libranzas y compromisos de pago por nómina.\n"
            "Instrucción de Seguridad: Para consultas específicas de saldos, recuerda al usuario que debe ingresar con su cédula y clave al Portal Transaccional oficial por seguridad.\n"
             "Si el usuario cambia de tema, utiliza la función CompleteOrEscalate para devolver el control al Asistente Primario.\n"
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
            "Eres el asesor experto en Vivienda de COOTRADECUN. Tu objetivo es ayudar a los asociados a cumplir el sueño de tener vivienda propia.\n"
            "Áreas de especialidad:\n"
            "- Proyectos: Información sobre 'Rancho Grande' (Melgar), 'El Pedregal' (Fusagasugá) y 'Arayanes de Peñalisa'.\n"
            "- Crédito: Explicación de montos (hasta 250 SMMLV), plazos (hasta 120 meses) y tasas preferenciales para asociados.\n"
            "- Simulación: Invitar al usuario a usar el simulador de crédito de vivienda en la web.\n"
            "Reglas: Si el usuario tiene dudas administrativas generales no relacionadas con vivienda, usa CompleteOrEscalate.\n"
            "\nCurrent time: {time}."
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

vivienda_tools = [consultar_vivienda, CompleteOrEscalate]
vivienda_runnable = vivienda_prompt | llm.bind_tools(vivienda_tools)


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
    return END

builder.add_conditional_edges(
    "primary_assistant",
    route_primary,
    ["enter_atencion_asociado", "enter_nominas", "enter_vivienda", END]
)

graph = builder.compile()
