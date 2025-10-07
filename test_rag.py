"""
Script de prueba para verificar el funcionamiento del RAG
Prueba que el sistema encuentra correctamente los FAQs
"""
import requests
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api"

def print_separator():
    """Imprime una línea separadora"""
    print("\n" + "=" * 70 + "\n")

def send_message(message: str, session_id: str = "test_rag") -> Dict[Any, Any]:
    """Envía un mensaje al chatbot"""
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
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def test_horarios():
    """Prueba búsqueda de horarios"""
    print_separator()
    print("🧪 TEST 1: Búsqueda de Horarios")
    print_separator()
    
    queries = [
        "¿Cuáles son los horarios de atención?",
        "¿A qué hora abren?",
        "¿Cuándo atienden?",
        "horario de oficina"
    ]
    
    for query in queries:
        print(f"👤 Usuario: {query}")
        result = send_message(query, "test_horarios")
        response = result['response'].lower()
        
        print(f"🤖 Bot: {result['response'][:200]}...")
        
        # Verificar que mencione horarios
        horario_keywords = ["8:00", "5:00", "lunes", "viernes", "sábado", "horario"]
        found = any(keyword in response for keyword in horario_keywords)
        
        if found:
            print("✅ ÉXITO: El bot encontró información de horarios")
        else:
            print("❌ FALLO: El bot NO encontró información de horarios")
        
        print_separator()

def test_all_faqs():
    """Prueba búsqueda de todos los FAQs"""
    print_separator()
    print("🧪 TEST 2: Búsqueda de Todos los FAQs")
    print_separator()
    
    # Lista de preguntas que corresponden a cada FAQ del markdown
    faq_tests = [
        {
            "query": "¿Cuáles son los horarios de atención?",
            "expected_keywords": ["8:00", "5:00", "lunes", "viernes", "sábado"],
            "topic": "Horarios"
        },
        {
            "query": "¿Qué beneficios tiene ser afiliado?",
            "expected_keywords": ["crédito", "ahorro", "seguro", "beneficio"],
            "topic": "Beneficios"
        },
        {
            "query": "¿Cuáles son los requisitos para solicitar un crédito?",
            "expected_keywords": ["6 meses", "antigüedad", "aporte", "cédula"],
            "topic": "Requisitos Créditos"
        },
        {
            "query": "¿Qué tipos de crédito hay disponibles?",
            "expected_keywords": ["libre inversión", "vivienda", "educativo", "vehículo"],
            "topic": "Tipos de Crédito"
        },
        {
            "query": "¿Cuál es el aporte mínimo mensual?",
            "expected_keywords": ["2%", "salario", "aporte"],
            "topic": "Aportes Mínimos"
        },
        {
            "query": "¿Cómo me afilio a Cootradecun?",
            "expected_keywords": ["18 años", "formulario", "cédula", "aporte"],
            "topic": "Proceso de Afiliación"
        },
        {
            "query": "¿Cómo consulto mi estado de cuenta?",
            "expected_keywords": ["oficina virtual", "www.cootradecun.com", "línea"],
            "topic": "Consulta Estado"
        },
        {
            "query": "¿Qué son los auxilios educativos?",
            "expected_keywords": ["educativo", "primaria", "secundaria", "universitario"],
            "topic": "Auxilios Educativos"
        },
        {
            "query": "¿Cuáles son las tasas de interés?",
            "expected_keywords": ["12.5%", "10%", "8%", "11%", "tasa"],
            "topic": "Tasas de Interés"
        },
        {
            "query": "¿Qué seguros ofrece Cootradecun?",
            "expected_keywords": ["vida", "accidente", "exequial", "seguro"],
            "topic": "Seguros"
        },
        {
            "query": "¿Cómo retiro mis aportes?",
            "expected_keywords": ["30", "60", "días", "retiro", "formulario"],
            "topic": "Retiro de Aportes"
        },
        {
            "query": "¿Qué convenios comerciales tienen?",
            "expected_keywords": ["convenio", "100", "descuento", "comercial"],
            "topic": "Convenios"
        }
    ]
    
    results = []
    
    for test in faq_tests:
        query = test["query"]
        expected = test["expected_keywords"]
        topic = test["topic"]
        
        print(f"📝 Tema: {topic}")
        print(f"👤 Usuario: {query}")
        
        result = send_message(query, f"test_faq_{topic.replace(' ', '_').lower()}")
        response = result['response'].lower()
        
        print(f"🤖 Bot: {result['response'][:150]}...")
        
        # Verificar que contenga al menos una palabra clave
        found = any(keyword.lower() in response for keyword in expected)
        
        if found:
            print(f"✅ ÉXITO: Encontró información sobre {topic}")
            results.append(True)
        else:
            print(f"❌ FALLO: NO encontró información sobre {topic}")
            print(f"   Palabras clave esperadas: {', '.join(expected)}")
            results.append(False)
        
        print_separator()
    
    # Resumen
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print("\n📊 RESUMEN DE PRUEBAS RAG:")
    print(f"   Total de FAQs probados: {total}")
    print(f"   ✅ Encontrados correctamente: {passed}")
    print(f"   ❌ No encontrados: {failed}")
    print(f"   Tasa de éxito: {(passed/total)*100:.1f}%")
    
    return passed == total

def test_variations():
    """Prueba variaciones de las mismas preguntas"""
    print_separator()
    print("🧪 TEST 3: Variaciones de Consultas")
    print_separator()
    
    variations = [
        {
            "variations": [
                "horarios",
                "¿cuándo abren?",
                "¿qué días atienden?",
                "hora de atención"
            ],
            "topic": "Horarios (variaciones)"
        },
        {
            "variations": [
                "beneficios",
                "¿qué gano siendo afiliado?",
                "ventajas de afiliarme",
                "por qué afiliarme"
            ],
            "topic": "Beneficios (variaciones)"
        }
    ]
    
    results = []
    
    for test in variations:
        topic = test["topic"]
        print(f"\n📝 Tema: {topic}")
        
        for query in test["variations"]:
            print(f"   👤 {query}")
            result = send_message(query, "test_variations")
            response = result['response'].lower()
            
            # Verificar que no sea una respuesta de "no encontré"
            not_found_keywords = ["no encontré", "no tengo información", "no pude"]
            is_not_found = any(keyword in response for keyword in not_found_keywords)
            
            if not is_not_found:
                print(f"   ✅ Respondió")
                results.append(True)
            else:
                print(f"   ❌ No encontró información")
                results.append(False)
        
        print_separator()
    
    passed = sum(results)
    total = len(results)
    print(f"\n📊 Variaciones: {passed}/{total} respondidas correctamente ({(passed/total)*100:.1f}%)")
    
    return passed >= total * 0.8  # 80% de éxito es aceptable

def main():
    """Ejecuta todas las pruebas de RAG"""
    print("\n")
    print("=" * 70)
    print("  🔍 PRUEBAS DE RAG - CHATBOT COOTRADECUN")
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
        test_horarios()
        test2_passed = test_all_faqs()
        test3_passed = test_variations()
        
        # Resumen final
        print_separator()
        print("📊 RESUMEN GENERAL")
        print_separator()
        print(f"   Test 1 - Horarios: ✅ COMPLETADO")
        print(f"   Test 2 - Todos los FAQs: {'✅ PASÓ' if test2_passed else '❌ FALLÓ'}")
        print(f"   Test 3 - Variaciones: {'✅ PASÓ' if test3_passed else '❌ FALLÓ'}")
        
        if test2_passed and test3_passed:
            print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
            print("El sistema RAG está funcionando correctamente.")
        else:
            print("\n⚠️  ALGUNAS PRUEBAS FALLARON")
            print("Revisa los logs del servidor para más detalles.")
        
        print_separator()
        print("\n💡 Tip: Revisa los logs del servidor (consola donde corre run.py)")
        print("   para ver el detalle de qué documentos está encontrando el RAG.")
        print_separator()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Pruebas interrumpidas por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

