from typing import Annotated, Literal
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from .rag import get_retrievers

# --- Transfer Tools ---

class ToAtencionAsociado(BaseModel):
    """Transfers the conversation to the Associate Attention specialist."""
    request: str = Field(description="The user's specific query or need related to association, benefits, or agreements.")

class ToNominas(BaseModel):
    """Transfers the conversation to the Payroll and Payments specialist."""
    request: str = Field(description="The user's specific query or need related to payroll, payments, or deductions.")

class ToVivienda(BaseModel):
    """Transfers the conversation to the Housing specialist."""
    request: str = Field(description="The user's specific query or need related to housing projects or credits.")

class CompleteOrEscalate(BaseModel):
    """A tool to mark the current task as completed and/or to escalate control of the dialog to the main assistant,
    who can re-route the dialog based on the user's needs."""
    cancel: bool = True
    reason: str

    class Config:
        json_schema_extra = {
            "example": {
                "cancel": True,
                "reason": "User changed their mind about the current task.",
            },
            "example 2": {
                "cancel": True,
                "reason": "I have fully completed the task.",
            },
            "example 3": {
                "cancel": False,
                "reason": "I need to look up something else.",
            },
        }

# --- Retrieval Tools ---

@tool
def consultar_atencion_asociado(query: str):
    """Useful to answer questions about association requirements, benefits, auxiliaries, and agreements."""
    retrievers = get_retrievers()
    if "atencion_asociado" in retrievers:
        docs = retrievers["atencion_asociado"].invoke(query)
        return "\n\n".join([d.page_content for d in docs])
    return "No information available."

@tool
def consultar_nominas(query: str):
    """Useful to answer questions about payment slips, payment channels, and payroll deductions."""
    retrievers = get_retrievers()
    if "nominas" in retrievers:
        docs = retrievers["nominas"].invoke(query)
        return "\n\n".join([d.page_content for d in docs])
    return "No information available."

@tool
def consultar_vivienda(query: str):
    """Useful to answer questions about housing projects, credits, and simulations."""
    retrievers = get_retrievers()
    if "vivienda" in retrievers:
        docs = retrievers["vivienda"].invoke(query)
        return "\n\n".join([d.page_content for d in docs])
    return "No information available."
