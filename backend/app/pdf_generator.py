"""
Módulo para generación de certificados en formato PDF.
Usa ReportLab para crear PDFs profesionales.
"""

import os
from io import BytesIO
from datetime import datetime
from typing import Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


# Colores corporativos de Cootradecun
COLORS = {
    "primary": colors.HexColor('#1a365d'),      # Azul oscuro
    "secondary": colors.HexColor('#2c5282'),    # Azul medio
    "accent": colors.HexColor('#4299e1'),       # Azul claro
    "background": colors.HexColor('#ebf8ff'),   # Fondo azul muy claro
    "text": colors.HexColor('#2d3748'),         # Gris oscuro
    "success": colors.HexColor('#38a169'),      # Verde
}


def _get_styles() -> Dict[str, ParagraphStyle]:
    """Retorna los estilos personalizados para los PDFs."""
    base_styles = getSampleStyleSheet()
    
    return {
        "title": ParagraphStyle(
            'CustomTitle',
            parent=base_styles['Heading1'],
            fontSize=20,
            alignment=TA_CENTER,
            spaceAfter=20,
            spaceBefore=10,
            textColor=COLORS["primary"],
            fontName='Helvetica-Bold'
        ),
        "subtitle": ParagraphStyle(
            'Subtitle',
            parent=base_styles['Heading2'],
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=30,
            textColor=COLORS["secondary"]
        ),
        "heading": ParagraphStyle(
            'CustomHeading',
            parent=base_styles['Heading2'],
            fontSize=12,
            spaceAfter=10,
            spaceBefore=20,
            textColor=COLORS["primary"],
            fontName='Helvetica-Bold'
        ),
        "normal": ParagraphStyle(
            'CustomNormal',
            parent=base_styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            textColor=COLORS["text"]
        ),
        "footer": ParagraphStyle(
            'Footer',
            parent=base_styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        ),
        "note": ParagraphStyle(
            'Note',
            parent=base_styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER,
            spaceBefore=20
        ),
    }


def generar_certificado_tributario_pdf(datos: Dict[str, Any]) -> BytesIO:
    """
    Genera un certificado tributario en formato PDF.
    
    Args:
        datos: Diccionario con los datos del certificado
            
    Returns:
        BytesIO: Buffer con el PDF generado
    """
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=1*inch,
        leftMargin=1*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    styles = _get_styles()
    story = []
    
    # Header
    story.append(Paragraph("COOTRADECUN", styles["title"]))
    story.append(Paragraph(
        "Cooperativa Multiactiva de Trabajadores de la Educación",
        styles["subtitle"]
    ))
    
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=COLORS["primary"], spaceAfter=20))
    
    # Título del certificado
    story.append(Paragraph("CERTIFICADO TRIBUTARIO", styles["title"]))
    story.append(Paragraph(f"Año Gravable {datos['año_gravable']}", styles["subtitle"]))
    
    # Información del asociado
    story.append(Paragraph("INFORMACIÓN DEL ASOCIADO", styles["heading"]))
    
    info_data = [
        ['Nombre Completo:', datos['nombre']],
        ['Número de Cédula:', datos['cedula']],
        ['Fecha de Expedición:', datetime.now().strftime('%d de %B de %Y')],
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('TEXTCOLOR', (1, 0), (1, -1), COLORS["text"]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    # Detalle del certificado
    story.append(Paragraph("DETALLE DE INGRESOS Y DEDUCCIONES", styles["heading"]))
    
    table_data = [
        ['CONCEPTO', 'VALOR'],
        ['Ingresos Laborales', f"$ {datos['ingresos_laborales']:,.0f}"],
        ['Aportes Fondo de Pensiones (AFP)', f"- $ {datos['aportes_afp']:,.0f}"],
        ['Aportes a Salud (EPS)', f"- $ {datos['aportes_salud']:,.0f}"],
        ['Aportes a la Cooperativa', f"- $ {datos['aportes_cooperativa']:,.0f}"],
        ['Retención en la Fuente', f"- $ {datos['retencion_fuente']:,.0f}"],
    ]
    
    main_table = Table(table_data, colWidths=[4*inch, 2*inch])
    main_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLORS["primary"]),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 2), (-1, 2), COLORS["background"]),
        ('BACKGROUND', (0, 4), (-1, 4), COLORS["background"]),
    ]))
    story.append(main_table)
    story.append(Spacer(1, 10))
    
    # Total
    total_data = [['VALOR NETO CERTIFICADO', f"$ {datos['total_certificado']:,.0f}"]]
    total_table = Table(total_data, colWidths=[4*inch, 2*inch])
    total_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLORS["success"]),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 14),
        ('TOPPADDING', (0, 0), (-1, 0), 14),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('BOX', (0, 0), (-1, -1), 2, COLORS["success"]),
    ]))
    story.append(total_table)
    
    # Nota legal
    story.append(Spacer(1, 30))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey, spaceBefore=10, spaceAfter=10))
    
    story.append(Paragraph(
        f"Este certificado es válido para efectos de la declaración de renta "
        f"correspondiente al año gravable {datos['año_gravable']}, de conformidad "
        f"con lo establecido en el Estatuto Tributario.",
        styles["note"]
    ))
    
    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph(
        f"Documento generado electrónicamente el {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}",
        styles["footer"]
    ))
    story.append(Paragraph(
        "COOTRADECUN - NIT: 860.007.738-1 | Bogotá D.C., Colombia",
        styles["footer"]
    ))
    story.append(Paragraph(
        "Este documento no requiere firma por ser generado electrónicamente.",
        styles["footer"]
    ))
    
    doc.build(story)
    buffer.seek(0)
    
    return buffer
