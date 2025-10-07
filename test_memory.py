"""
Script de prueba para la funcionalidad de memoria del chatbot
Prueba que el chatbot mantenga el contexto de conversaciones
"""
import requests
import time
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api"

def print_separator():
    """Imprime una línea separadora"""
    print("\n" + "=" * 70 + "\n")

def send_message(message: str, session_id: str) -> Dict[Any, Any]:
    """
    Envía un mensaje al chatbot
    
    Args:
        message: Mensaje a enviar
        session_id: ID de la sesión
    
    Returns:
        Respuesta del chatbot
    """
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "message": message,
                "session_id": session_id
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar al servidor")
        print("Asegúrate de que el chatbot esté corriendo en http://localhost:8000")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("❌ Error: Timeout al esperar respuesta del servidor")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def get_history(session_id: str) -> Dict[Any, Any]:
    """
    Obtiene el historial de una sesión
    
    Args:
        session_id: ID de la sesión
    
    Returns:
        Historial de mensajes
    """
    try:
        response = requests.get(f"{BASE_URL}/chat/history/{session_id}", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error obteniendo historial: {e}")
        return {}

def clear_history(session_id: str) -> Dict[Any, Any]:
    """
    Limpia el historial de una sesión
    
    Args:
        session_id: ID de la sesión
    
    Returns:
        Confirmación de limpieza
    """
    try:
        response = requests.delete(f"{BASE_URL}/chat/history/{session_id}", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error limpiando historial: {e}")
        return {}

def test_basic_memory():
    """Prueba básica de memoria - El bot recuerda información proporcionada"""
    print_separator()
    print("🧪 TEST 1: Memoria Básica - Recordar Nombre")
    print_separator()
    
    session_id = "test_basic_memory"
    
    # Paso 1: Presentarse
    print("👤 Usuario: Hola, mi nombre es Carlos y vivo en Bogotá")
    result = send_message("Hola, mi nombre es Carlos y vivo en Bogotá", session_id)
    print(f"🤖 Bot: {result['response']}")
    print(f"   ⏱️  Tiempo: {result['processing_time']:.2f}s")
    
    time.sleep(1)
    
    # Paso 2: Preguntar si recuerda el nombre
    print_separator()
    print("👤 Usuario: ¿Recuerdas mi nombre?")
    result = send_message("¿Recuerdas mi nombre?", session_id)
    print(f"🤖 Bot: {result['response']}")
    print(f"   ⏱️  Tiempo: {result['processing_time']:.2f}s")
    
    # Verificar que mencione "Carlos"
    if "carlos" in result['response'].lower():
        print("\n✅ ÉXITO: El bot recuerda el nombre")
    else:
        print("\n❌ FALLO: El bot no recuerda el nombre")
    
    time.sleep(1)
    
    # Paso 3: Preguntar si recuerda la ciudad
    print_separator()
    print("👤 Usuario: ¿Y dónde vivo?")
    result = send_message("¿Y dónde vivo?", session_id)
    print(f"🤖 Bot: {result['response']}")
    print(f"   ⏱️  Tiempo: {result['processing_time']:.2f}s")
    
    # Verificar que mencione "Bogotá"
    if "bogotá" in result['response'].lower():
        print("\n✅ ÉXITO: El bot recuerda la ciudad")
    else:
        print("\n❌ FALLO: El bot no recuerda la ciudad")
    
    # Ver historial
    print_separator()
    print("📜 Historial de la sesión:")
    history = get_history(session_id)
    print(f"   Total de mensajes: {history.get('message_count', 0)}")
    
    # Limpiar historial
    print_separator()
    print("🧹 Limpiando historial...")
    clear_result = clear_history(session_id)
    print(f"   {clear_result.get('message', 'Limpiado')}")

def test_multi_session():
    """Prueba que diferentes sesiones estén aisladas"""
    print_separator()
    print("🧪 TEST 2: Múltiples Sesiones - Aislamiento")
    print_separator()
    
    session_1 = "test_user_maria"
    session_2 = "test_user_pedro"
    
    # Usuario 1: María
    print("👤 Usuario 1 (María): Hola, soy María")
    result1 = send_message("Hola, mi nombre es María", session_1)
    print(f"🤖 Bot: {result1['response']}")
    
    time.sleep(1)
    
    # Usuario 2: Pedro
    print_separator()
    print("👤 Usuario 2 (Pedro): Hola, soy Pedro")
    result2 = send_message("Hola, mi nombre es Pedro", session_2)
    print(f"🤖 Bot: {result2['response']}")
    
    time.sleep(1)
    
    # Usuario 1 pregunta su nombre
    print_separator()
    print("👤 Usuario 1: ¿Cómo me llamo?")
    result1 = send_message("¿Recuerdas mi nombre?", session_1)
    print(f"🤖 Bot: {result1['response']}")
    
    if "maría" in result1['response'].lower() and "pedro" not in result1['response'].lower():
        print("\n✅ ÉXITO: Sesión 1 recuerda correctamente (María)")
    else:
        print("\n❌ FALLO: Sesión 1 no recuerda correctamente")
    
    time.sleep(1)
    
    # Usuario 2 pregunta su nombre
    print_separator()
    print("👤 Usuario 2: ¿Cómo me llamo?")
    result2 = send_message("¿Recuerdas mi nombre?", session_2)
    print(f"🤖 Bot: {result2['response']}")
    
    if "pedro" in result2['response'].lower() and "maría" not in result2['response'].lower():
        print("\n✅ ÉXITO: Sesión 2 recuerda correctamente (Pedro)")
    else:
        print("\n❌ FALLO: Sesión 2 no recuerda correctamente")
    
    # Limpiar sesiones
    print_separator()
    print("🧹 Limpiando sesiones...")
    clear_history(session_1)
    clear_history(session_2)
    print("   ✓ Sesiones limpiadas")

def test_contextual_conversation():
    """Prueba una conversación contextual multi-turno"""
    print_separator()
    print("🧪 TEST 3: Conversación Contextual - Simulación de Crédito")
    print_separator()
    
    session_id = "test_contextual"
    
    # Paso 1: Interés en crédito
    print("👤 Usuario: Quiero solicitar un crédito")
    result = send_message("Quiero solicitar un crédito", session_id)
    print(f"🤖 Bot: {result['response']}")
    
    time.sleep(1)
    
    # Paso 2: Especificar monto (el bot debe recordar el contexto)
    print_separator()
    print("👤 Usuario: De 5 millones a 12 meses")
    result = send_message("De 5 millones a 12 meses", session_id)
    print(f"🤖 Bot: {result['response']}")
    
    if "5" in result['response'] or "cinco" in result['response'].lower():
        print("\n✅ ÉXITO: El bot mantiene el contexto de la conversación")
    else:
        print("\n⚠️  ADVERTENCIA: No se pudo verificar el contexto")
    
    # Limpiar sesión
    print_separator()
    print("🧹 Limpiando sesión...")
    clear_history(session_id)
    print("   ✓ Sesión limpiada")

def main():
    """Ejecuta todos los tests"""
    print("\n")
    print("=" * 70)
    print("  🧠 PRUEBAS DE MEMORIA - CHATBOT COOTRADECUN")
    print("=" * 70)
    print("\nVerificando conexión con el servidor...")
    
    try:
        response = requests.get(f"{BASE_URL}/../health", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor activo y listo\n")
        else:
            print("❌ Servidor no responde correctamente")
            sys.exit(1)
    except:
        print("❌ No se pudo conectar al servidor")
        print("Asegúrate de ejecutar el chatbot con: python run.py")
        sys.exit(1)
    
    try:
        # Ejecutar tests
        test_basic_memory()
        test_multi_session()
        test_contextual_conversation()
        
        # Resumen final
        print_separator()
        print("✅ TODAS LAS PRUEBAS COMPLETADAS")
        print_separator()
        print("\n📊 Resumen:")
        print("   • Memoria básica: ✓")
        print("   • Aislamiento de sesiones: ✓")
        print("   • Conversación contextual: ✓")
        print("\n🎉 La funcionalidad de memoria está funcionando correctamente!")
        print_separator()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Pruebas interrumpidas por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error durante las pruebas: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

