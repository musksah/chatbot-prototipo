"""
Script de inicio rápido para el chatbot Cootradecun
"""
import uvicorn
import os
from dotenv import load_dotenv

# Cargar variables de entorno
try:
    load_dotenv()
except UnicodeDecodeError:
    print("\n⚠️  ERROR: Archivo .env tiene codificación incorrecta")
    print("El archivo .env debe estar en UTF-8 sin BOM\n")
    print("Solución:")
    print("1. Elimina el archivo .env")
    print("2. Créalo de nuevo con un editor como VS Code o Notepad++")
    print("3. Asegúrate de guardar como UTF-8\n")
    input("Presiona Enter para continuar de todos modos...")
except Exception as e:
    print(f"⚠️  Advertencia al cargar .env: {e}")

if __name__ == "__main__":
    # Verificar que exista OPENAI_API_KEY
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("=" * 60)
        print("⚠️  ADVERTENCIA: OPENAI_API_KEY no configurada")
        print("=" * 60)
        print("\nPor favor, crea un archivo .env con tu API key:")
        print("OPENAI_API_KEY=sk-tu-api-key-aqui\n")
        print("O configúrala como variable de entorno del sistema.\n")
        response = input("¿Deseas continuar de todos modos? (s/n): ")
        if response.lower() != 's':
            exit(0)
    
    # Configuración del servidor
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print("\n" + "=" * 60)
    print("🚀 Iniciando Chatbot Cootradecun")
    print("=" * 60)
    print(f"\n✅ Servidor corriendo en: http://{host}:{port}")
    print(f"✅ Interfaz web: http://localhost:{port}")
    print(f"✅ Documentación API: http://localhost:{port}/docs")
    print(f"✅ Health check: http://localhost:{port}/health")
    print("\n" + "=" * 60 + "\n")
    
    # Iniciar servidor
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

