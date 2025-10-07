"""
Script de diagnóstico para ChromaDB - Chatbot Cootradecun
Revisa qué documentos están almacenados y prueba búsquedas
"""
import logging
from pathlib import Path
import sys
import os

# Configurar codificación UTF-8 para Windows
if sys.platform == "win32":
    os.system('chcp 65001 > nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def diagnose_chromadb():
    """Diagnóstico completo de ChromaDB"""
    
    print("\n" + "=" * 80)
    print("[DIAGNOSTICO] CHROMADB - CHATBOT COOTRADECUN")
    print("=" * 80 + "\n")
    
    try:
        # Importar después de configurar logging
        from app.agents.tools.rag_tool import initialize_rag, collection, rag_search
        
        print("[PASO 1] Inicializando RAG...")
        print("-" * 80)
        initialize_rag()
        
        if collection is None:
            print("[ERROR] Collection no inicializada\n")
            return
        
        # Obtener información de la colección
        count = collection.count()
        print(f"[OK] Coleccion inicializada: '{collection.name}'")
        print(f"[INFO] Total de documentos: {count}\n")
        
        if count == 0:
            print("[WARNING] No hay documentos en la coleccion!\n")
            return
        
        # Obtener todos los documentos
        print("=" * 80)
        print("[PASO 2] TODOS LOS DOCUMENTOS EN CHROMADB")
        print("=" * 80 + "\n")
        
        all_docs = collection.get()
        
        if not all_docs or not all_docs.get("ids"):
            print("[ERROR] No se pudieron obtener documentos\n")
            return
        
        ids = all_docs["ids"]
        documents = all_docs["documents"]
        metadatas = all_docs.get("metadatas", [])
        
        for i, (doc_id, doc_text, metadata) in enumerate(zip(ids, documents, metadatas), 1):
            print(f"\n{'-' * 80}")
            print(f"[DOCUMENTO {i}/{len(ids)}]")
            print(f"{'-' * 80}")
            print(f"ID: {doc_id}")
            print(f"Titulo: {metadata.get('title', 'Sin titulo')}")
            print(f"Categoria: {metadata.get('category', 'N/A')}")
            print(f"Tema: {metadata.get('topic', 'N/A')}")
            print(f"\nCONTENIDO COMPLETO:")
            print("-" * 80)
            print(doc_text)
            print("-" * 80)
            print(f"Longitud: {len(doc_text)} caracteres")
        
        # Pruebas de búsqueda
        print("\n" + "=" * 80)
        print("[PASO 3] PRUEBAS DE BUSQUEDA")
        print("=" * 80 + "\n")
        
        test_queries = [
            "horarios",
            "horarios de atención",
            "¿cuáles son los horarios?",
            "¿a qué hora atienden?",
            "horas de atención",
            "Horarios de Atención",
            "beneficios",
            "créditos",
            "requisitos"
        ]
        
        for query in test_queries:
            print(f"\n{'-' * 80}")
            print(f"[QUERY] '{query}'")
            print(f"{'-' * 80}")
            
            # Búsqueda directa en ChromaDB
            results = collection.query(
                query_texts=[query],
                n_results=3
            )
            
            if results and results["documents"] and results["documents"][0]:
                docs = results["documents"][0]
                ids = results["ids"][0]
                metadatas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0]
                
                print(f"[OK] Encontrados {len(docs)} resultados:")
                
                for i, (doc_id, doc, meta, dist) in enumerate(zip(ids, docs, metadatas, distances), 1):
                    title = meta.get("title", "Sin titulo") if meta else "Sin titulo"
                    print(f"\n   {i}. [{doc_id}] {title}")
                    print(f"      Distancia: {dist:.4f}")
                    print(f"      Preview: {doc[:200]}...")
            else:
                print("[ERROR] No se encontraron resultados")
            
            # Probar también con la función rag_search
            print(f"\n   [TEST] Probando con rag_search()...")
            rag_result = rag_search(query, top_k=3)
            
            if rag_result.get("found"):
                print(f"   [OK] RAG Search exitoso")
                print(f"   Respuesta: {rag_result['answer'][:200]}...")
            else:
                print(f"   [ERROR] RAG Search fallo: {rag_result.get('answer', 'Sin respuesta')}")
        
        # Análisis de similitud
        print("\n" + "=" * 80)
        print("[PASO 4] ANALISIS DE SIMILITUD SEMANTICA")
        print("=" * 80 + "\n")
        
        # Buscar específicamente "horarios"
        horarios_results = collection.query(
            query_texts=["horarios de atención"],
            n_results=count  # Traer todos
        )
        
        print("[TARGET] Busqueda: 'horarios de atencion' (todos los resultados ordenados):\n")
        
        if horarios_results and horarios_results["documents"] and horarios_results["documents"][0]:
            docs = horarios_results["documents"][0]
            ids = horarios_results["ids"][0]
            metadatas = horarios_results.get("metadatas", [[]])[0]
            distances = horarios_results.get("distances", [[]])[0]
            
            for i, (doc_id, meta, dist) in enumerate(zip(ids, metadatas, distances), 1):
                title = meta.get("title", "Sin titulo") if meta else "Sin titulo"
                category = meta.get("category", "N/A") if meta else "N/A"
                
                relevance = "[MUY RELEVANTE]" if dist < 0.5 else "[RELEVANTE]" if dist < 1.0 else "[POCO RELEVANTE]"
                
                print(f"   {i}. {relevance}")
                print(f"      ID: {doc_id}")
                print(f"      Titulo: {title}")
                print(f"      Categoria: {category}")
                print(f"      Distancia: {dist:.4f}")
                print()
        
        # Verificar archivo fuente
        print("=" * 80)
        print("[PASO 5] VERIFICACION DEL ARCHIVO FUENTE")
        print("=" * 80 + "\n")
        
        faq_path = Path(__file__).parent / "app" / "data" / "faqs_cootradecun.md"
        
        if faq_path.exists():
            print(f"[OK] Archivo encontrado: {faq_path}")
            print(f"Tamanio: {faq_path.stat().st_size} bytes")
            
            with open(faq_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            print(f"Lineas: {len(content.splitlines())}")
            print(f"\n[SEARCH] Buscando 'Horarios' en el archivo...")
            
            lines = content.splitlines()
            for i, line in enumerate(lines, 1):
                if "horario" in line.lower():
                    print(f"   Linea {i}: {line}")
        else:
            print(f"[ERROR] Archivo NO encontrado: {faq_path}")
        
        print("\n" + "=" * 80)
        print("[OK] DIAGNOSTICO COMPLETADO")
        print("=" * 80 + "\n")
        
    except Exception as e:
        logger.error(f"[ERROR] Error en diagnostico: {e}", exc_info=True)
        print(f"\n[ERROR] {e}\n")


if __name__ == "__main__":
    diagnose_chromadb()

