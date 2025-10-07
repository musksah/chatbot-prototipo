"""
Script de prueba para verificar el funcionamiento del chatbot
"""
import asyncio
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
import logging
logging.basicConfig(level=logging.INFO)

async def test_chatbot():
    """
    Prueba el chatbot con varios mensajes de ejemplo
    """
    from app.agents.graph import chatbot_graph
    from langchain_core.messages import HumanMessage
    
    print("\n" + "=" * 60)
    print("🧪 Pruebas del Chatbot Cootradecun")
    print("=" * 60 + "\n")
    
    # Verificar que el grafo esté inicializado
    if chatbot_graph is None:
        print("❌ Error: El grafo del chatbot no está inicializado")
        print("Verifica que OPENAI_API_KEY esté configurada correctamente\n")
        return
    
    # Mensajes de prueba
    test_messages = [
        "Hola, ¿cuáles son los horarios de atención?",
        "¿Qué beneficios tiene ser afiliado?",
        "Quiero simular un crédito de 5000000 a 12 meses",
        "¿Cuál es el estado del afiliado con cédula 12345678?",
        "Necesito un certificado para la cédula 87654321"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{'─' * 60}")
        print(f"Prueba {i}/{len(test_messages)}")
        print(f"{'─' * 60}")
        print(f"👤 Usuario: {message}")
        
        try:
            # Ejecutar el grafo
            input_state = {
                "messages": [HumanMessage(content=message)]
            }
            
            result = chatbot_graph.invoke(input_state)
            
            # Extraer respuesta
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                response = last_message.content if hasattr(last_message, 'content') else str(last_message)
                print(f"\n🤖 Bot: {response}")
            else:
                print("\n❌ No se recibió respuesta")
                
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
        
        # Pausa entre mensajes
        await asyncio.sleep(1)
    
    print("\n" + "=" * 60)
    print("✅ Pruebas completadas")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    # Verificar API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n❌ Error: OPENAI_API_KEY no configurada")
        print("\nCrea un archivo .env con:")
        print("OPENAI_API_KEY=sk-tu-api-key-aqui\n")
        exit(1)
    
    # Ejecutar pruebas
    asyncio.run(test_chatbot())

