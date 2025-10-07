"""
Script de prueba para verificar las restricciones del chatbot
Verifica que el bot rechace preguntas fuera del contexto de Cootradecun
"""
import requests
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api"

def print_separator():
    """Imprime una línea separadora"""
    print("\n" + "=" * 70 + "\n")

def send_message(message: str, session_id: str = "test_restrictions") -> Dict[Any, Any]:
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

def test_out_of_scope_questions():
    """Prueba que el bot rechace preguntas fuera de alcance"""
    print_separator()
    print("🧪 TEST: Restricciones - Preguntas Fuera de Contexto")
    print_separator()
    
    # Lista de preguntas fuera de contexto que deben ser rechazadas
    out_of_scope_questions = [
        {
            "question": "¿Cuál es la receta para hacer un flan?",
            "category": "Recetas de cocina"
        },
        {
            "question": "¿Quién ganó el mundial de fútbol en 2022?",
            "category": "Deportes"
        },
        {
            "question": "¿Cómo puedo perder peso rápidamente?",
            "category": "Salud general"
        },
        {
            "question": "Dame consejos para viajar a Europa",
            "category": "Turismo"
        },
        {
            "question": "¿Cuál es la capital de Francia?",
            "category": "Geografía"
        },
        {
            "question": "Explícame cómo funciona la fotosíntesis",
            "category": "Ciencia"
        }
    ]
    
    results = []
    
    for item in out_of_scope_questions:
        question = item["question"]
        category = item["category"]
        
        print(f"📝 Categoría: {category}")
        print(f"👤 Usuario: {question}")
        
        result = send_message(question)
        response = result['response'].lower()
        
        print(f"🤖 Bot: {result['response'][:150]}...")
        
        # Verificar que la respuesta indica restricción
        restriction_keywords = [
            "lo siento",
            "solo puedo ayudarte",
            "especializado en",
            "cootradecun",
            "cooperativa",
            "no puedo",
            "fuera de mi alcance"
        ]
        
        is_restricted = any(keyword in response for keyword in restriction_keywords)
        
        if is_restricted:
            print("✅ CORRECTO: El bot rechazó la pregunta fuera de contexto")
            results.append(True)
        else:
            print("❌ ERROR: El bot respondió una pregunta fuera de contexto")
            results.append(False)
        
        print_separator()
    
    # Resumen
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print("\n📊 RESUMEN DE PRUEBAS DE RESTRICCIÓN:")
    print(f"   Total de preguntas: {total}")
    print(f"   ✅ Rechazadas correctamente: {passed}")
    print(f"   ❌ Respondidas incorrectamente: {failed}")
    print(f"   Tasa de éxito: {(passed/total)*100:.1f}%")
    
    return passed == total

def test_in_scope_questions():
    """Prueba que el bot responda preguntas dentro del alcance"""
    print_separator()
    print("🧪 TEST: Preguntas Válidas - Dentro del Contexto")
    print_separator()
    
    # Lista de preguntas válidas que deben ser respondidas
    in_scope_questions = [
        {
            "question": "¿Cuáles son los horarios de atención de Cootradecun?",
            "expected_keywords": ["horario", "lunes", "viernes", "atención"]
        },
        {
            "question": "¿Qué beneficios tiene ser afiliado?",
            "expected_keywords": ["beneficio", "crédito", "ahorro", "seguro"]
        },
        {
            "question": "¿Cuáles son los requisitos para solicitar un crédito?",
            "expected_keywords": ["requisito", "meses", "antigüedad", "aporte", "crédito"]
        },
        {
            "question": "¿Cómo puedo consultar mi estado de cuenta?",
            "expected_keywords": ["consultar", "estado", "oficina", "web"]
        }
    ]
    
    results = []
    
    for item in in_scope_questions:
        question = item["question"]
        expected = item["expected_keywords"]
        
        print(f"👤 Usuario: {question}")
        
        result = send_message(question)
        response = result['response'].lower()
        
        print(f"🤖 Bot: {result['response'][:200]}...")
        
        # Verificar que la respuesta contenga palabras clave relevantes
        has_relevant_content = any(keyword in response for keyword in expected)
        
        # Verificar que NO sea una respuesta de restricción
        restriction_keywords = ["lo siento", "solo puedo ayudarte con", "no puedo"]
        is_restriction = any(keyword in response for keyword in restriction_keywords)
        
        if has_relevant_content and not is_restriction:
            print("✅ CORRECTO: El bot respondió la pregunta válida")
            results.append(True)
        else:
            print("❌ ERROR: El bot no respondió adecuadamente la pregunta válida")
            results.append(False)
        
        print_separator()
    
    # Resumen
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print("\n📊 RESUMEN DE PREGUNTAS VÁLIDAS:")
    print(f"   Total de preguntas: {total}")
    print(f"   ✅ Respondidas correctamente: {passed}")
    print(f"   ❌ No respondidas correctamente: {failed}")
    print(f"   Tasa de éxito: {(passed/total)*100:.1f}%")
    
    return passed == total

def test_edge_cases():
    """Prueba casos límite"""
    print_separator()
    print("🧪 TEST: Casos Límite")
    print_separator()
    
    edge_cases = [
        {
            "question": "Hola",
            "should_respond": True,
            "description": "Saludo simple"
        },
        {
            "question": "¿Qué sabes hacer?",
            "should_respond": True,
            "description": "Pregunta sobre capacidades"
        },
        {
            "question": "Ayúdame con mi tarea de matemáticas",
            "should_respond": False,
            "description": "Tarea escolar"
        }
    ]
    
    results = []
    
    for case in edge_cases:
        question = case["question"]
        should_respond = case["should_respond"]
        description = case["description"]
        
        print(f"📝 Caso: {description}")
        print(f"👤 Usuario: {question}")
        
        result = send_message(question)
        response = result['response'].lower()
        
        print(f"🤖 Bot: {result['response'][:150]}...")
        
        restriction_keywords = ["lo siento", "solo puedo ayudarte", "no puedo"]
        is_restriction = any(keyword in response for keyword in restriction_keywords)
        
        if should_respond:
            # Debe responder sin restricción
            if not is_restriction:
                print("✅ CORRECTO: El bot respondió apropiadamente")
                results.append(True)
            else:
                print("❌ ERROR: El bot restringió una pregunta válida")
                results.append(False)
        else:
            # Debe restringir
            if is_restriction:
                print("✅ CORRECTO: El bot rechazó apropiadamente")
                results.append(True)
            else:
                print("❌ ERROR: El bot respondió una pregunta que debió rechazar")
                results.append(False)
        
        print_separator()
    
    total = len(results)
    passed = sum(results)
    
    print(f"\n📊 CASOS LÍMITE: {passed}/{total} correctos")
    
    return passed == total

def main():
    """Ejecuta todas las pruebas"""
    print("\n")
    print("=" * 70)
    print("  🔒 PRUEBAS DE RESTRICCIONES - CHATBOT COOTRADECUN")
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
        # Ejecutar todos los tests
        test1_passed = test_out_of_scope_questions()
        test2_passed = test_in_scope_questions()
        test3_passed = test_edge_cases()
        
        # Resumen final
        print_separator()
        print("📊 RESUMEN GENERAL")
        print_separator()
        print(f"   Test 1 - Restricciones: {'✅ PASÓ' if test1_passed else '❌ FALLÓ'}")
        print(f"   Test 2 - Preguntas válidas: {'✅ PASÓ' if test2_passed else '❌ FALLÓ'}")
        print(f"   Test 3 - Casos límite: {'✅ PASÓ' if test3_passed else '❌ FALLÓ'}")
        
        if test1_passed and test2_passed and test3_passed:
            print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
            print("El chatbot está correctamente restringido al contexto de Cootradecun.")
        else:
            print("\n⚠️  ALGUNAS PRUEBAS FALLARON")
            print("Revisa el system prompt o ajusta las restricciones.")
        
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

