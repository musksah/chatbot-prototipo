"""Test para verificar que el loader de markdown funciona"""
from app.agents.tools.rag_tool import _parse_markdown_faqs, initialize_rag
from pathlib import Path

print("=" * 60)
print("Test de carga de FAQs desde Markdown")
print("=" * 60)

# Probar parseo del archivo
markdown_path = Path('app/data/faqs_cootradecun.md')
print(f"\n1. Parseando archivo: {markdown_path}")
print(f"   Existe: {markdown_path.exists()}")

faqs = _parse_markdown_faqs(markdown_path)
print(f"\n2. FAQs parseados: {len(faqs)}")

for i, faq in enumerate(faqs, 1):
    print(f"\n   FAQ #{i}:")
    print(f"   - ID: {faq['id']}")
    print(f"   - Titulo: {faq['title']}")
    print(f"   - Texto: {faq['text'][:100]}...")
    print(f"   - Categoria: {faq['metadata']['category']}")
    print(f"   - Tema: {faq['metadata']['topic']}")

print(f"\n3. Inicializando ChromaDB con los FAQs...")
initialize_rag()

print("\n" + "=" * 60)
print("OK - Test completado exitosamente")
print("=" * 60)

