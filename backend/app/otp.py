"""
OTP Module - Twilio Verify WhatsApp Integration

Este módulo maneja la autenticación OTP usando Twilio Verify API vía WhatsApp.
"""

import os
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Twilio credentials from environment
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_VERIFY_SERVICE_SID = os.getenv("TWILIO_VERIFY_SERVICE_SID")

# Check if Twilio is configured
def is_twilio_configured() -> bool:
    """Check if Twilio credentials are configured."""
    return all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_VERIFY_SERVICE_SID])


def send_otp(phone_number: str) -> Tuple[bool, str]:
    """
    Envía un código OTP via SMS usando Twilio Verify.
    
    Args:
        phone_number: Número de teléfono en formato E.164 (ej: +573001234567)
    
    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    if not is_twilio_configured():
        logger.warning("Twilio credentials not configured. Using mock mode.")
        return True, "MOCK: OTP enviado (modo de prueba sin Twilio configurado)"
    
    try:
        from twilio.rest import Client
        
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        verification = client.verify.v2 \
            .services(TWILIO_VERIFY_SERVICE_SID) \
            .verifications.create(
                to=phone_number,
                channel="sms"
            )
        
        if verification.status == "pending":
            logger.info(f"OTP sent successfully to {phone_number[-4:]}")
            return True, f"Código de verificación enviado por SMS al número terminado en {phone_number[-4:]}"
        else:
            logger.error(f"OTP send failed with status: {verification.status}")
            return False, f"Error al enviar el código: {verification.status}"
            
    except Exception as e:
        error_msg = f"Error sending OTP to {phone_number}: {type(e).__name__}: {str(e)}"
        print(f"🔴 TWILIO ERROR: {error_msg}")  # Direct print for visibility
        logger.error(error_msg)
        # Si es un error de Twilio, mostrar más detalles
        if hasattr(e, 'code'):
            print(f"🔴 Twilio error code: {e.code}")
            logger.error(f"Twilio error code: {e.code}")
        if hasattr(e, 'msg'):
            print(f"🔴 Twilio error message: {e.msg}")
            logger.error(f"Twilio error message: {e.msg}")
        return False, f"Error al enviar el código de verificación: {str(e)}"


def verify_otp(phone_number: str, code: str) -> Tuple[bool, str]:
    """
    Verifica el código OTP ingresado por el usuario.
    
    Args:
        phone_number: Número de teléfono en formato E.164
        code: Código de 6 dígitos ingresado por el usuario
    
    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    if not is_twilio_configured():
        logger.warning("Twilio credentials not configured. Using mock mode.")
        # En modo mock, aceptar cualquier código de 6 dígitos que sea "123456"
        if code == "123456":
            return True, "MOCK: Verificación exitosa (modo de prueba)"
        else:
            return False, "MOCK: Código incorrecto. Usa '123456' en modo de prueba."
    
    try:
        from twilio.rest import Client
        
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        verification_check = client.verify.v2 \
            .services(TWILIO_VERIFY_SERVICE_SID) \
            .verification_checks.create(
                to=phone_number,
                code=code
            )
        
        if verification_check.status == "approved":
            logger.info(f"OTP verified successfully for {phone_number[-4:]}")
            return True, "✅ Verificación exitosa"
        else:
            logger.warning(f"OTP verification failed: {verification_check.status}")
            return False, "❌ Código incorrecto o expirado. Por favor, solicita un nuevo código."
            
    except Exception as e:
        logger.error(f"Error verifying OTP: {str(e)}")
        return False, f"Error al verificar el código: {str(e)}"


def format_phone_number(phone: str, country_code: str = "+57") -> str:
    """
    Formatea un número de teléfono al formato E.164.
    
    Args:
        phone: Número de teléfono (puede tener o no código de país)
        country_code: Código de país por defecto (Colombia = +57)
    
    Returns:
        str: Número en formato E.164
    """
    # Remover espacios y caracteres no numéricos excepto +
    cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
    
    # Si ya tiene código de país, retornar
    if cleaned.startswith('+'):
        return cleaned
    
    # Si empieza con 0, removerlo
    if cleaned.startswith('0'):
        cleaned = cleaned[1:]
    
    # Agregar código de país
    return f"{country_code}{cleaned}"
