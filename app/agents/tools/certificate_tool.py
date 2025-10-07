"""
Certificate Tool - Generación de certificados PDF para afiliados
"""
from typing import Dict
from langchain.tools import tool
import logging
from datetime import datetime
from jinja2 import Template
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Template HTML para el certificado
CERTIFICATE_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <style>
        @page {
            size: letter;
            margin: 2cm;
        }
        body {
            font-family: 'Arial', sans-serif;
            color: #333;
            line-height: 1.6;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 3px solid #1e3a8a;
            padding-bottom: 20px;
        }
        .logo {
            font-size: 28px;
            font-weight: bold;
            color: #1e3a8a;
        }
        .title {
            font-size: 24px;
            font-weight: bold;
            color: #1e3a8a;
            margin: 30px 0 20px 0;
            text-align: center;
        }
        .content {
            margin: 30px 0;
            text-align: justify;
        }
        .info-box {
            background-color: #f3f4f6;
            padding: 20px;
            border-left: 4px solid #1e3a8a;
            margin: 20px 0;
        }
        .info-row {
            margin: 10px 0;
        }
        .label {
            font-weight: bold;
            color: #1e3a8a;
        }
        .footer {
            margin-top: 60px;
            text-align: center;
            font-size: 12px;
            color: #666;
        }
        .signature {
            margin-top: 80px;
            text-align: center;
        }
        .signature-line {
            border-top: 2px solid #333;
            width: 300px;
            margin: 0 auto 10px auto;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">COOTRADECUN</div>
        <div>Cooperativa de Trabajadores de Cundinamarca</div>
        <div style="font-size: 12px; color: #666;">NIT: 800.123.456-7</div>
    </div>
    
    <div class="title">CERTIFICADO DE AFILIACIÓN</div>
    
    <div class="content">
        <p>La Cooperativa de Trabajadores de Cundinamarca - <strong>COOTRADECUN</strong>, 
        certifica que:</p>
    </div>
    
    <div class="info-box">
        <div class="info-row">
            <span class="label">Nombre:</span> {{ nombre }}
        </div>
        <div class="info-row">
            <span class="label">Cédula:</span> {{ cedula }}
        </div>
        <div class="info-row">
            <span class="label">Estado:</span> {{ estado }}
        </div>
        <div class="info-row">
            <span class="label">Fecha de afiliación:</span> {{ fecha_afiliacion }}
        </div>
        <div class="info-row">
            <span class="label">Aportes:</span> {{ estado_aportes }}
        </div>
    </div>
    
    <div class="content">
        <p>Se encuentra registrado(a) como asociado(a) activo(a) de nuestra cooperativa, 
        gozando de todos los derechos y beneficios establecidos en nuestros estatutos.</p>
        
        <p>Este certificado se expide a solicitud del interesado para los fines que 
        estime convenientes.</p>
    </div>
    
    <div class="signature">
        <div class="signature-line"></div>
        <div><strong>Gerente General</strong></div>
        <div>COOTRADECUN</div>
    </div>
    
    <div class="footer">
        <p><strong>Fecha de expedición:</strong> {{ fecha_expedicion }}</p>
        <p>Código de verificación: {{ codigo_verificacion }}</p>
        <p style="margin-top: 20px;">
            Dirección: Calle 100 #10-20, Bogotá D.C. | Teléfono: (601) 555-0100<br>
            www.cootradecun.com | info@cootradecun.com
        </p>
    </div>
</body>
</html>
"""


@tool("generate_certificate")
def generate_certificate(cedula: str, tipo: str = "afiliacion") -> Dict:
    """
    Genera un certificado PDF para un afiliado de Cootradecun.
    
    Args:
        cedula: Número de cédula del afiliado
        tipo: Tipo de certificado (por defecto "afiliacion")
    
    Returns:
        Dict con información del certificado generado
    """
    try:
        logger.info(f"Generando certificado: cedula={cedula}, tipo={tipo}")
        
        # Importar WeasyPrint solo si es necesario (puede ser pesado)
        try:
            from weasyprint import HTML
        except ImportError:
            logger.warning("WeasyPrint no disponible, generando certificado simulado")
            return _generate_mock_certificate(cedula, tipo)
        
        # Datos mock del afiliado (en producción vendría de Linix)
        from .linix_tools import MOCK_MEMBERS
        
        if cedula not in MOCK_MEMBERS:
            return {
                "success": False,
                "message": f"No se encontró afiliado con cédula {cedula}"
            }
        
        member = MOCK_MEMBERS[cedula]
        
        # Preparar datos para el template
        context = {
            "nombre": member["nombre"],
            "cedula": member["cedula"],
            "estado": member["estado"].upper(),
            "fecha_afiliacion": member["fecha_afiliacion"],
            "estado_aportes": "AL DÍA" if member["aportes_al_dia"] else "PENDIENTE",
            "fecha_expedicion": datetime.now().strftime("%d de %B de %Y"),
            "codigo_verificacion": f"CERT-{cedula}-{datetime.now().strftime('%Y%m%d')}"
        }
        
        # Renderizar template
        template = Template(CERTIFICATE_TEMPLATE)
        html_content = template.render(**context)
        
        # Crear directorio de salida si no existe
        output_dir = Path("app/data/generated")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generar PDF
        filename = f"certificado_{cedula}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = output_dir / filename
        
        HTML(string=html_content).write_pdf(output_path)
        
        logger.info(f"Certificado generado: {output_path}")
        
        return {
            "success": True,
            "certificate": {
                "filename": filename,
                "path": str(output_path),
                "tipo": tipo,
                "afiliado": member["nombre"],
                "fecha_generacion": context["fecha_expedicion"],
                "codigo": context["codigo_verificacion"]
            },
            "message": f"✅ Certificado generado exitosamente para {member['nombre']}"
        }
        
    except Exception as e:
        logger.error(f"Error en generate_certificate: {e}")
        return {
            "success": False,
            "message": f"Error al generar certificado: {str(e)}"
        }


def _generate_mock_certificate(cedula: str, tipo: str) -> Dict:
    """
    Genera un certificado simulado cuando WeasyPrint no está disponible
    """
    from .linix_tools import MOCK_MEMBERS
    
    if cedula not in MOCK_MEMBERS:
        return {
            "success": False,
            "message": f"No se encontró afiliado con cédula {cedula}"
        }
    
    member = MOCK_MEMBERS[cedula]
    codigo = f"CERT-{cedula}-{datetime.now().strftime('%Y%m%d')}"
    
    return {
        "success": True,
        "certificate": {
            "filename": f"certificado_{cedula}.pdf",
            "path": "simulado",
            "tipo": tipo,
            "afiliado": member["nombre"],
            "fecha_generacion": datetime.now().strftime("%d de %B de %Y"),
            "codigo": codigo
        },
        "message": f"✅ Certificado simulado para {member['nombre']} (código: {codigo}). En producción se generaría el PDF real.",
        "note": "WeasyPrint no está instalado. Instálalo para generar PDFs reales."
    }

