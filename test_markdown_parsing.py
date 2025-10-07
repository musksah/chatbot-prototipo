"""
Script de diagnóstico para verificar el parsing del archivo markdown
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar el módulo
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.tools.rag_tool import _parse_markdown_faqs

def test_parsing():
    """Prueba el parsing del archivo markdown"""
    print("\n" + "=" * 70)
    print("  📄 DIAGNÓSTICO DE PARSING - faqs_cootradecun.md")
    print("=" * 70 + "\n")
    
    # Ruta al archivo
    markdown_path = Path("app/data/faqs_cootradecun.md")
    
    if not markdown_path.exists():
        print(f"❌ Error: No se encontró el archivo {markdown_path}")
        return
    
    print(f"✅ Archivo encontrado: {markdown_path}")
    print(f"   Tamaño: {markdown_path.stat().st_size} bytes\n")
    
    # Parsear el archivo
    print("🔍 Parseando archivo...\n")
    faqs = _parse_markdown_faqs(markdown_path)
    
    if not faqs:
        print("❌ ERROR: No se parsearon FAQs del archivo")
        print("   Verifica el formato del archivo markdown")
        return
    
    print(f"✅ Se parsearon {len(faqs)} FAQs correctamente\n")
    print("=" * 70)
    
    # Mostrar cada FAQ parseado
    for i, faq in enumerate(faqs, 1):
        print(f"\n📝 FAQ #{i}: {faq['id']}")
        print(f"   Título: {faq['title']}")
        print(f"   Categoría: {faq['metadata']['category']}")
        print(f"   Tema: {faq['metadata']['topic']}")
        print(f"   Contenido (primeros 100 caracteres):")
        print(f"   {faq['text'][:100]}...")
        print(f"   Longitud total: {len(faq['text'])} caracteres")
    
    print("\n" + "=" * 70)
    print("\n📊 RESUMEN:")
    print(f"   Total de FAQs: {len(faqs)}")
    
    # Contar por categoría
    categories = {}
    for faq in faqs:
        cat = faq['metadata']['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n   Distribución por categoría:")
    for cat, count in categories.items():
        print(f"   - {cat}: {count} FAQs")
    
    print("\n" + "=" * 70)
    
    # Verificar el FAQ de horarios específicamente
    print("\n🔍 VERIFICACIÓN ESPECÍFICA: FAQ de Horarios")
    print("=" * 70)
    
    horarios_faq = next((f for f in faqs if "horario" in f['title'].lower()), None)
    
    if horarios_faq:
        print("✅ FAQ de horarios encontrado:")
        print(f"   ID: {horarios_faq['id']}")
        print(f"   Título: {horarios_faq['title']}")
        print(f"   Contenido completo:")
        print(f"   {horarios_faq['text']}")
        print("\n✅ El FAQ de horarios está correctamente parseado")
    else:
        print("❌ ERROR: No se encontró el FAQ de horarios")
        print("   Verifica el formato en el archivo markdown")
    
    print("\n" + "=" * 70)
    print("\n✅ Diagnóstico completado")
    print("\n💡 Si los FAQs se parsearon correctamente pero el RAG no los encuentra:")
    print("   1. Reinicia el servidor (python run.py)")
    print("   2. Ejecuta: python test_rag.py")
    print("   3. Revisa los logs del servidor para ver qué está buscando ChromaDB")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    test_parsing()

