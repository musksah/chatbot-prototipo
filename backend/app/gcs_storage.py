"""
Módulo para gestión de archivos en Google Cloud Storage.
Provee funcionalidades para subir PDFs y generar URLs firmadas.
"""

import os
import logging
from datetime import timedelta
from typing import Optional, Tuple
from io import BytesIO

logger = logging.getLogger(__name__)

# Configuración del bucket (desde variables de entorno)
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "cootradecun-certificados")
GCS_PROJECT_ID = os.getenv("GCP_PROJECT_ID", None)

# Tiempo de expiración de URLs firmadas (en horas)
SIGNED_URL_EXPIRATION_HOURS = int(os.getenv("SIGNED_URL_EXPIRATION_HOURS", "24"))


def _get_storage_client():
    """
    Obtiene el cliente de Cloud Storage.
    Usa las credenciales por defecto del entorno (ADC).
    """
    try:
        from google.cloud import storage
        if GCS_PROJECT_ID:
            return storage.Client(project=GCS_PROJECT_ID)
        return storage.Client()
    except Exception as e:
        logger.error(f"Error al crear cliente de GCS: {e}")
        raise


def is_gcs_configured() -> bool:
    """Verifica si GCS está configurado correctamente."""
    try:
        client = _get_storage_client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        return bucket.exists()
    except Exception as e:
        logger.warning(f"GCS no está configurado: {e}")
        return False


def upload_pdf_to_gcs(
    pdf_buffer: BytesIO, 
    filename: str,
    folder: str = "certificados"
) -> Tuple[bool, str]:
    """
    Sube un PDF a Google Cloud Storage.
    
    Args:
        pdf_buffer: Buffer con el contenido del PDF
        filename: Nombre del archivo (sin extensión)
        folder: Carpeta dentro del bucket
        
    Returns:
        Tuple[bool, str]: (éxito, mensaje o blob_name)
    """
    try:
        from google.cloud import storage
        from google.cloud.exceptions import GoogleCloudError
        
        client = _get_storage_client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        
        blob_name = f"{folder}/{filename}.pdf"
        blob = bucket.blob(blob_name)
        
        blob.content_type = "application/pdf"
        blob.metadata = {
            "generated_by": "cootradecun-chatbot",
            "document_type": folder
        }
        
        pdf_buffer.seek(0)
        blob.upload_from_file(pdf_buffer, content_type="application/pdf")
        
        logger.info(f"PDF subido exitosamente: gs://{GCS_BUCKET_NAME}/{blob_name}")
        
        return True, blob_name
        
    except Exception as e:
        logger.error(f"Error al subir PDF a GCS: {e}")
        return False, f"Error al subir archivo: {str(e)}"


def generate_signed_url(
    blob_name: str,
    expiration_hours: Optional[int] = None
) -> Tuple[bool, str]:
    """
    Genera una URL firmada para descargar un archivo de GCS.
    
    En Cloud Run con ADC (Application Default Credentials), usa IAM-based signing
    que requiere el rol 'roles/iam.serviceAccountTokenCreator' en el Service Account.
    
    Args:
        blob_name: Nombre completo del blob (incluyendo carpeta)
        expiration_hours: Horas hasta que expire la URL (default: 24)
        
    Returns:
        Tuple[bool, str]: (éxito, URL firmada o mensaje de error)
    """
    try:
        import google.auth
        from google.auth.transport import requests as auth_requests
        
        client = _get_storage_client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(blob_name)
        
        if not blob.exists():
            return False, "El archivo no existe en el almacenamiento"
        
        hours = expiration_hours or SIGNED_URL_EXPIRATION_HOURS
        expiration = timedelta(hours=hours)
        
        # Get credentials
        credentials, project = google.auth.default()
        
        # Refresh credentials to ensure we have a valid token
        auth_request = auth_requests.Request()
        credentials.refresh(auth_request)
        
        # Get service account email - try from credentials first, then env var
        sa_email = getattr(credentials, 'service_account_email', None)
        if not sa_email or sa_email == 'default':
            sa_email = os.getenv("SERVICE_ACCOUNT_EMAIL")
        
        if not sa_email:
            return False, "No se pudo determinar el email de la cuenta de servicio. Configure SERVICE_ACCOUNT_EMAIL."
        
        logger.info(f"Generando URL firmada con SA: {sa_email}, token exists: {bool(credentials.token)}")
        
        # Use IAM-based signing with service_account_email and access_token
        # This invokes the IAM signBlob API under the hood
        url = blob.generate_signed_url(
            version="v4",
            expiration=expiration,
            method="GET",
            response_disposition=f'attachment; filename="{blob_name.split("/")[-1]}"',
            service_account_email=sa_email,
            access_token=credentials.token
        )
        
        logger.info(f"URL firmada generada para: {blob_name} (expira en {hours}h)")
        
        return True, url
        
    except Exception as e:
        logger.error(f"Error al generar URL firmada: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False, f"Error al generar URL: {str(e)}"


def upload_and_get_signed_url(
    pdf_buffer: BytesIO,
    filename: str,
    folder: str = "certificados",
    expiration_hours: Optional[int] = None
) -> Tuple[bool, str]:
    """
    Función de conveniencia: sube un PDF y retorna su URL firmada.
    
    Args:
        pdf_buffer: Buffer con el contenido del PDF
        filename: Nombre del archivo (sin extensión)
        folder: Carpeta dentro del bucket
        expiration_hours: Horas hasta que expire la URL
        
    Returns:
        Tuple[bool, str]: (éxito, URL firmada o mensaje de error)
    """
    success, result = upload_pdf_to_gcs(pdf_buffer, filename, folder)
    
    if not success:
        return False, result
    
    blob_name = result
    return generate_signed_url(blob_name, expiration_hours)


# === Modo de desarrollo local (sin GCS) ===

LOCAL_PDF_DIR = os.path.join(os.path.dirname(__file__), "..", "generated_pdfs")


def save_pdf_locally(pdf_buffer: BytesIO, filename: str) -> str:
    """
    Guarda un PDF localmente (para desarrollo).
    
    Args:
        pdf_buffer: Buffer con el contenido del PDF
        filename: Nombre del archivo
        
    Returns:
        str: Ruta al archivo guardado
    """
    os.makedirs(LOCAL_PDF_DIR, exist_ok=True)
    
    filepath = os.path.join(LOCAL_PDF_DIR, f"{filename}.pdf")
    
    pdf_buffer.seek(0)
    with open(filepath, 'wb') as f:
        f.write(pdf_buffer.read())
    
    logger.info(f"PDF guardado localmente: {filepath}")
    return filepath
