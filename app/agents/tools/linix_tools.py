"""
Linix Tools - Herramientas mock para simular consultas al sistema Linix
(Sistema de gestión de afiliados de Cootradecun)
"""
from typing import Dict
from langchain.tools import tool
import logging
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

# Base de datos mock de afiliados (para demostración)
MOCK_MEMBERS = {
    "12345678": {
        "nombre": "Juan Pérez García",
        "cedula": "12345678",
        "fecha_afiliacion": "2020-03-15",
        "estado": "activo",
        "aportes_al_dia": True,
        "saldo_aportes": 15_750_000,
        "ultimo_aporte": "2024-09-30",
        "creditos_activos": 1,
        "cupo_disponible": 25_000_000
    },
    "87654321": {
        "nombre": "María Rodríguez López",
        "cedula": "87654321",
        "fecha_afiliacion": "2019-06-20",
        "estado": "activo",
        "aportes_al_dia": True,
        "saldo_aportes": 22_500_000,
        "ultimo_aporte": "2024-09-30",
        "creditos_activos": 0,
        "cupo_disponible": 40_000_000
    }
}


@tool("get_member_status")
def get_member_status(cedula: str) -> Dict:
    """
    Consulta el estado de afiliación y aportes de un asociado en el sistema Linix.
    
    Args:
        cedula: Número de cédula del afiliado
    
    Returns:
        Dict con información del estado del afiliado
    """
    try:
        logger.info(f"Consultando estado de afiliado: {cedula}")
        
        # Buscar en base de datos mock
        if cedula in MOCK_MEMBERS:
            member = MOCK_MEMBERS[cedula]
            
            return {
                "success": True,
                "found": True,
                "data": {
                    "nombre": member["nombre"],
                    "cedula": member["cedula"],
                    "estado": member["estado"],
                    "fecha_afiliacion": member["fecha_afiliacion"],
                    "aportes_al_dia": member["aportes_al_dia"],
                    "saldo_aportes": f"${member['saldo_aportes']:,.0f}",
                    "ultimo_aporte": member["ultimo_aporte"],
                    "creditos_activos": member["creditos_activos"],
                    "cupo_disponible": f"${member['cupo_disponible']:,.0f}"
                },
                "message": f"Información encontrada para {member['nombre']}"
            }
        else:
            # Si no existe, devolver datos de ejemplo
            return {
                "success": True,
                "found": False,
                "message": f"No se encontró afiliado con cédula {cedula}. Esta es una simulación - en producción se consultaría el sistema Linix real."
            }
            
    except Exception as e:
        logger.error(f"Error en get_member_status: {e}")
        return {
            "success": False,
            "found": False,
            "message": f"Error al consultar el sistema: {str(e)}"
        }


@tool("simulate_credit")
def simulate_credit(monto: float, plazo_meses: int, tasa_anual: float = 12.5) -> Dict:
    """
    Simula un crédito calculando la cuota mensual y el total a pagar.
    
    Args:
        monto: Monto del crédito solicitado en pesos colombianos
        plazo_meses: Plazo del crédito en meses
        tasa_anual: Tasa de interés anual (por defecto 12.5%)
    
    Returns:
        Dict con la simulación del crédito
    """
    try:
        logger.info(f"Simulando crédito: monto={monto}, plazo={plazo_meses} meses")
        
        # Validaciones básicas
        if monto <= 0:
            return {
                "success": False,
                "message": "El monto debe ser mayor a cero"
            }
        
        if plazo_meses <= 0 or plazo_meses > 120:
            return {
                "success": False,
                "message": "El plazo debe estar entre 1 y 120 meses"
            }
        
        # Calcular tasa mensual
        tasa_mensual = tasa_anual / 12 / 100
        
        # Calcular cuota mensual usando fórmula de amortización
        if tasa_mensual > 0:
            cuota_mensual = monto * (tasa_mensual * (1 + tasa_mensual) ** plazo_meses) / \
                           ((1 + tasa_mensual) ** plazo_meses - 1)
        else:
            cuota_mensual = monto / plazo_meses
        
        # Calcular total a pagar
        total_pagar = cuota_mensual * plazo_meses
        total_intereses = total_pagar - monto
        
        # Fecha estimada de primera cuota (siguiente mes)
        fecha_primera_cuota = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        return {
            "success": True,
            "simulacion": {
                "monto_solicitado": f"${monto:,.0f}",
                "plazo_meses": plazo_meses,
                "tasa_anual": f"{tasa_anual}%",
                "tasa_mensual": f"{tasa_mensual * 100:.2f}%",
                "cuota_mensual": f"${cuota_mensual:,.0f}",
                "total_pagar": f"${total_pagar:,.0f}",
                "total_intereses": f"${total_intereses:,.0f}",
                "fecha_primera_cuota": fecha_primera_cuota
            },
            "message": "Simulación realizada exitosamente. Esta es una cotización preliminar.",
            "nota": "Para solicitar el crédito debes estar al día en tus aportes y cumplir con los requisitos establecidos."
        }
        
    except Exception as e:
        logger.error(f"Error en simulate_credit: {e}")
        return {
            "success": False,
            "message": f"Error al simular crédito: {str(e)}"
        }


@tool("check_credit_eligibility")
def check_credit_eligibility(cedula: str, monto_solicitado: float) -> Dict:
    """
    Verifica si un afiliado es elegible para un crédito específico.
    
    Args:
        cedula: Número de cédula del afiliado
        monto_solicitado: Monto del crédito solicitado
    
    Returns:
        Dict con información de elegibilidad
    """
    try:
        logger.info(f"Verificando elegibilidad: cedula={cedula}, monto={monto_solicitado}")
        
        # Consultar estado del afiliado
        if cedula not in MOCK_MEMBERS:
            return {
                "success": True,
                "eligible": False,
                "message": "Afiliado no encontrado en el sistema"
            }
        
        member = MOCK_MEMBERS[cedula]
        
        # Verificar requisitos
        reasons = []
        
        if member["estado"] != "activo":
            reasons.append("El estado de afiliación no está activo")
        
        if not member["aportes_al_dia"]:
            reasons.append("Tiene aportes pendientes")
        
        # Verificar antigüedad (mínimo 6 meses)
        fecha_afiliacion = datetime.strptime(member["fecha_afiliacion"], "%Y-%m-%d")
        meses_antiguedad = (datetime.now() - fecha_afiliacion).days / 30
        if meses_antiguedad < 6:
            reasons.append(f"Antigüedad insuficiente ({meses_antiguedad:.0f} meses, se requieren 6)")
        
        # Verificar cupo disponible
        if monto_solicitado > member["cupo_disponible"]:
            reasons.append(f"Monto solicitado excede el cupo disponible (${member['cupo_disponible']:,.0f})")
        
        eligible = len(reasons) == 0
        
        if eligible:
            return {
                "success": True,
                "eligible": True,
                "data": {
                    "nombre": member["nombre"],
                    "cupo_aprobado": f"${member['cupo_disponible']:,.0f}",
                    "antiguedad_meses": int(meses_antiguedad),
                    "estado_aportes": "Al día"
                },
                "message": f"✅ {member['nombre']} es elegible para el crédito solicitado"
            }
        else:
            return {
                "success": True,
                "eligible": False,
                "reasons": reasons,
                "message": "No cumple con los requisitos para el crédito"
            }
            
    except Exception as e:
        logger.error(f"Error en check_credit_eligibility: {e}")
        return {
            "success": False,
            "eligible": False,
            "message": f"Error al verificar elegibilidad: {str(e)}"
        }

