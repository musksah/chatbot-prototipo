from typing import Annotated, Literal
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from .rag import _invoke_retriever_with_logging
import logging

logger = logging.getLogger(__name__)

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

class ToConvenios(BaseModel):
    """Transfers the conversation to the Agreements/Partnerships specialist."""
    request: str = Field(description="The user's specific query about partner companies, discounts, benefits, or commercial agreements.")

class ToCartera(BaseModel):
    """Transfers the conversation to the Loans/Portfolio specialist."""
    request: str = Field(description="The user's specific query about loans, credits, debt status, payments, or portfolio management.")

class ToContabilidad(BaseModel):
    """Transfers the conversation to the Accounting specialist for questions about suppliers, invoices, withholdings, and tax certificates."""
    request: str = Field(description="The user's query about supplier registration, invoicing, withholdings, or accounting certificates.")

class ToTesoreria(BaseModel):
    """Transfers the conversation to the Treasury/Payments specialist for questions about payment methods, disbursements, and bank accounts."""
    request: str = Field(description="The user's query about payment methods, bank accounts, disbursement times, or correspondents.")

class ToCredito(BaseModel):
    """Transfers the conversation to the Credit specialist for questions about loan types, requirements, and credit applications."""
    request: str = Field(description="The user's query about credit types, loan requirements, credit simulation, or credit applications.")

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

# Query expansion: Gemini generates alternative phrasings for broader retrieval
from langchain_google_genai import ChatGoogleGenerativeAI
from .rag import search_by_department, _hybrid_search, _rerank_chunks, _format_output, DEFAULT_K, RERANK_CANDIDATES, ENABLE_RERANK

ENABLE_QUERY_EXPANSION = True


def _expand_query(query: str) -> list[str]:
    """
    Use Gemini to generate 2 alternative phrasings of the user's query.
    This helps retrieve chunks that may use different terminology.
    
    Returns: list of 2-3 queries (original + alternatives)
    """
    if not ENABLE_QUERY_EXPANSION:
        return [query]
    
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.3)
        prompt = (
            f"Eres un asistente de búsqueda para COOTRADECUN (una cooperativa colombiana). "
            f"Genera exactamente 2 reformulaciones alternativas de la siguiente pregunta "
            f"para mejorar la búsqueda semántica. Las alternativas deben usar sinónimos "
            f"o frases diferentes pero mantener el mismo significado.\n\n"
            f"Pregunta original: {query}\n\n"
            f"Responde SOLO con las 2 alternativas, una por línea, sin numeración ni viñetas."
        )
        
        result = llm.invoke(prompt)
        alternatives = [
            line.strip() for line in result.content.strip().split("\n") 
            if line.strip()
        ][:2]  # Max 2 alternatives
        
        all_queries = [query] + alternatives
        logger.info(
            f"🔍 [EXPAND] Original: '{query[:50]}...' → "
            f"+{len(alternatives)} alternatives"
        )
        return all_queries
    
    except Exception as e:
        logger.warning(f"🔍 [EXPAND] Error expanding query: {e}. Using original only.")
        return [query]


def _invoke_retriever_with_expansion(department: str, query: str, k: int = DEFAULT_K) -> str:
    """
    Full RAG pipeline with query expansion:
    1. Expand query into 2-3 variants
    2. Run hybrid search for each variant
    3. Deduplicate candidates
    4. Re-rank all candidates
    5. Return top-k formatted results
    """
    # Step 1: Expand query
    queries = _expand_query(query)
    
    # Step 2: Hybrid search for each query
    all_candidates = []
    seen_ids = set()
    
    for q in queries:
        chunks = _hybrid_search(q, department, k=RERANK_CANDIDATES)
        for chunk in chunks:
            if chunk["id"] not in seen_ids:
                seen_ids.add(chunk["id"])
                all_candidates.append(chunk)
    
    if not all_candidates:
        return "No se encontró información relevante."
    
    # Step 3: Re-rank the combined pool using original query
    if ENABLE_RERANK and len(all_candidates) > k:
        final_chunks = _rerank_chunks(query, all_candidates, top_k=k)
    else:
        # Sort by RRF score as fallback
        all_candidates.sort(key=lambda c: c["rrf_score"], reverse=True)
        final_chunks = all_candidates[:k]
    
    # Step 4: Format output
    from .rag import DEPT_TO_TITLE
    result = _format_output(final_chunks, department)
    
    total_chars = sum(len(c["content"]) for c in final_chunks)
    logger.info(
        f"📚 [RAG+EXPAND] {department}: queries={len(queries)}, "
        f"total_candidates={len(all_candidates)}, final={len(final_chunks)}, "
        f"chars={total_chars}"
    )
    
    return result


@tool
def consultar_atencion_asociado(query: str):
    """Useful to answer questions about association requirements, benefits, auxiliaries, and agreements."""
    return _invoke_retriever_with_expansion("atencion_asociado", query)

@tool
def consultar_nominas(query: str):
    """Useful to answer questions about payment slips, payment channels, and payroll deductions."""
    return _invoke_retriever_with_expansion("nominas", query)

@tool
def consultar_vivienda(query: str):
    """Useful to answer questions about housing projects, credits, and simulations."""
    return _invoke_retriever_with_expansion("vivienda", query)

@tool
def consultar_convenios(query: str):
    """Useful to answer questions about partner companies, commercial agreements, discounts, and benefits for associates."""
    return _invoke_retriever_with_expansion("convenios", query)

@tool
def consultar_cartera(query: str):
    """Useful to answer questions about loans, credits, debt status, payment plans, and portfolio management."""
    return _invoke_retriever_with_expansion("cartera", query)

@tool
def consultar_contabilidad(query: str):
    """Useful to answer questions about supplier registration, invoicing, withholdings, and accounting certificates."""
    return _invoke_retriever_with_expansion("contabilidad", query)

@tool
def consultar_tesoreria(query: str):
    """Useful to answer questions about payment methods, bank accounts, disbursement times, and correspondents."""
    return _invoke_retriever_with_expansion("tesoreria", query)

@tool
def consultar_credito(query: str):
    """Useful to answer questions about credit types, loan requirements, credit simulation, and credit applications."""
    return _invoke_retriever_with_expansion("credito", query)


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


# Número fijo para envío de OTP (Colombia)
FIXED_OTP_PHONE = "+573024682891"

@tool
def solicitar_otp(cedula: str) -> str:
    """
    Solicita el envío de un código OTP por WhatsApp para verificar la identidad del usuario.
    Usar cuando el usuario proporcione su cédula para obtener un certificado.
    El OTP se envía automáticamente al número registrado del sistema.
    
    Args:
        cedula: Número de cédula del usuario
    
    Returns:
        Mensaje indicando si el OTP fue enviado exitosamente
    """
    # Store state with fixed phone number
    _otp_state[cedula] = {
        "phone": FIXED_OTP_PHONE,
        "verified": False
    }
    
    # Send OTP to fixed number
    success, message = send_otp(FIXED_OTP_PHONE)
    
    if success:
        return f"📱 Se ha enviado un código de verificación. Por favor, pide al usuario que ingrese el código de 6 dígitos que recibió."
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
    Genera el certificado tributario en formato PDF para el usuario autenticado.
    SOLO usar después de que el usuario haya sido verificado exitosamente con OTP.
    
    El certificado se genera como PDF y se sube a Google Cloud Storage,
    retornando una URL de descarga que expira en 24 horas.
    
    Args:
        cedula: Número de cédula del usuario autenticado
    
    Returns:
        Mensaje con el enlace de descarga del certificado PDF
    """
    import logging
    from datetime import datetime
    
    logger = logging.getLogger(__name__)
    
    # Check if user is verified
    if cedula not in _otp_state or not _otp_state[cedula].get("verified", False):
        return "❌ El usuario no ha sido verificado. Debes solicitar y verificar el OTP primero."
    
    try:
        # Import PDF and GCS modules
        from .pdf_generator import generar_certificado_tributario_pdf
        from .gcs_storage import upload_and_get_signed_url, save_pdf_locally, is_gcs_configured
        
        # Get certificate data (in production, this would call a real API/WebService)
        cert = CERTIFICADO_TRIBUTARIO_FAKE.copy()
        cert["cedula"] = cedula
        
        # Generate PDF
        pdf_buffer = generar_certificado_tributario_pdf(cert)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"certificado_tributario_{cedula}_{timestamp}"
        
        # Try to upload to GCS, fallback to local storage
        if is_gcs_configured():
            success, result = upload_and_get_signed_url(
                pdf_buffer,
                filename,
                folder="certificados_tributarios"
            )
            
            if success:
                # Clear OTP state
                del _otp_state[cedula]
                
                logger.info(f"Certificado tributario generado y subido a GCS para cédula {cedula}")
                
                return (
                    f"¡Tu certificado tributario ha sido generado con éxito! ✅\n\n"
                    f"Haz clic en el botón para descargarlo:\n\n"
                    f"{result}\n\n"
                    f"⏰ Este enlace estará disponible por 24 horas."
                )
            else:
                logger.warning(f"Error subiendo a GCS, usando almacenamiento local: {result}")
        
        # Fallback: save locally
        filepath = save_pdf_locally(pdf_buffer, filename)
        
        # Clear OTP state
        del _otp_state[cedula]
        
        logger.info(f"Certificado tributario generado localmente para cédula {cedula}")
        
        return (
            f"✅ **Certificado Tributario generado exitosamente**\n\n"
            f"📄 El archivo PDF se ha generado correctamente.\n"
            f"📂 Ubicación: `{filepath}`\n\n"
            f"_Nota: Para obtener una URL de descarga, configure Google Cloud Storage._"
        )
        
    except Exception as e:
        logger.error(f"Error generando certificado tributario: {e}")
        return f"❌ Error al generar el certificado: {str(e)}"

