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


# --- Transfer Tool for Certificates ---

class ToCertificados(BaseModel):
    """Transfers the conversation to the Certificates specialist for generating tax certificates and other official documents that require authentication."""
    request: str = Field(description="The user's request for a certificate (e.g., tax certificate, membership certificate).")


# --- OTP and Certificate Tools ---

from .otp import send_otp, verify_otp, format_phone_number

# In-memory storage for OTP state (in production, use Redis or database)
_otp_state = {}

# Fake certificate data
CERTIFICADO_TRIBUTARIO_FAKE = {
    "nombre": "JUAN CARLOS PÉREZ RODRÍGUEZ",
    "cedula": "1234567890",
    "año_gravable": 2024,
    "ingresos_laborales": 48000000,
    "aportes_afp": 1920000,
    "aportes_salud": 1920000,
    "aportes_cooperativa": 2400000,
    "retencion_fuente": 1200000,
    "total_certificado": 42560000
}


@tool
def solicitar_otp(cedula: str, telefono: str) -> str:
    """
    Solicita el envío de un código OTP por WhatsApp para verificar la identidad del usuario.
    Usar cuando el usuario proporcione su cédula y teléfono para obtener un certificado.
    
    Args:
        cedula: Número de cédula del usuario
        telefono: Número de teléfono del usuario (puede ser con o sin código de país)
    
    Returns:
        Mensaje indicando si el OTP fue enviado exitosamente
    """
    # Format phone number
    phone_formatted = format_phone_number(telefono)
    
    # Store state
    _otp_state[cedula] = {
        "phone": phone_formatted,
        "verified": False
    }
    
    # Send OTP
    success, message = send_otp(phone_formatted)
    
    if success:
        return f"📱 {message}. Por favor, pide al usuario que ingrese el código de 6 dígitos que recibió."
    else:
        return f"❌ {message}"


@tool
def verificar_codigo_otp(cedula: str, codigo: str) -> str:
    """
    Verifica el código OTP ingresado por el usuario.
    Usar cuando el usuario proporcione el código de 6 dígitos recibido por WhatsApp.
    
    Args:
        cedula: Número de cédula del usuario (para recuperar el teléfono asociado)
        codigo: Código de 6 dígitos ingresado por el usuario
    
    Returns:
        Mensaje indicando si la verificación fue exitosa
    """
    if cedula not in _otp_state:
        return "❌ No hay una solicitud de OTP pendiente para esta cédula. Por favor, solicita un nuevo código."
    
    phone = _otp_state[cedula]["phone"]
    success, message = verify_otp(phone, codigo)
    
    if success:
        _otp_state[cedula]["verified"] = True
        return f"{message}. El usuario está autenticado. Ahora puedes generar el certificado."
    else:
        return message


@tool
def generar_certificado_tributario(cedula: str) -> str:
    """
    Genera el certificado tributario para el usuario autenticado.
    SOLO usar después de que el usuario haya sido verificado exitosamente con OTP.
    
    Args:
        cedula: Número de cédula del usuario autenticado
    
    Returns:
        El certificado tributario formateado
    """
    # Check if user is verified
    if cedula not in _otp_state or not _otp_state[cedula].get("verified", False):
        return "❌ El usuario no ha sido verificado. Debes solicitar y verificar el OTP primero."
    
    # Generate fake certificate (in production, this would call a real API)
    cert = CERTIFICADO_TRIBUTARIO_FAKE.copy()
    cert["cedula"] = cedula  # Use the actual cedula provided
    
    # Format the certificate
    certificate_text = f"""
📄 **CERTIFICADO TRIBUTARIO - AÑO {cert['año_gravable']}**
═══════════════════════════════════════════════

**Nombre:** {cert['nombre']}
**Cédula:** {cert['cedula']}

| Concepto | Valor |
|----------|-------|
| Ingresos Laborales | ${cert['ingresos_laborales']:,.0f} |
| Aportes AFP | -${cert['aportes_afp']:,.0f} |
| Aportes Salud | -${cert['aportes_salud']:,.0f} |
| Aportes Cooperativa | -${cert['aportes_cooperativa']:,.0f} |
| Retención en Fuente | -${cert['retencion_fuente']:,.0f} |

═══════════════════════════════════════════════
**TOTAL CERTIFICADO:** ${cert['total_certificado']:,.0f}

_Este certificado es válido para efectos de la declaración de renta del año gravable {cert['año_gravable']}._
"""
    
    # Clear the OTP state after generating certificate
    del _otp_state[cedula]
    
    return certificate_text
