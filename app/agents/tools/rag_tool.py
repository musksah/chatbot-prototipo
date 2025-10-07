"""
RAG Tool - Búsqueda semántica en la base de conocimiento de Cootradecun
"""
from typing import Dict
from langchain.tools import tool
import chromadb
from chromadb.config import Settings
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Cliente global de ChromaDB (in-memory para el prototipo)
chroma_client = None
collection = None


def initialize_rag():
    """Inicializa ChromaDB y la colección con datos de ejemplo"""
    global chroma_client, collection
    
    try:
        chroma_client = chromadb.Client(Settings(
            anonymized_telemetry=False,
            allow_reset=True
        ))
        
        # Crear o obtener colección
        collection = chroma_client.get_or_create_collection(
            name="cootradecun_faqs",
            metadata={"description": "FAQs y documentación de Cootradecun"}
        )
        
        # Agregar datos de ejemplo si la colección está vacía
        if collection.count() == 0:
            _load_sample_data()
            
        logger.info(f"RAG inicializado: {collection.count()} documentos cargados")
        
    except Exception as e:
        logger.error(f"Error inicializando RAG: {e}")
        raise


def _parse_markdown_faqs(markdown_path: Path) -> list:
    """
    Parsea un archivo markdown y extrae los FAQs.
    
    Formato esperado:
    ## Título del FAQ
    Contenido del FAQ...
    **Categoría**: categoria
    **Tema**: tema
    ---
    
    Args:
        markdown_path: Ruta al archivo markdown
    
    Returns:
        Lista de diccionarios con id, text, metadata
    """
    try:
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Dividir por separadores ---
        sections = content.split('---')
        faqs = []
        faq_counter = 0
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Si la sección empieza con '# ' (cabecera principal), extraer solo la parte después
            if section.startswith('# '):
                # Buscar donde empieza el primer ## dentro de esta sección
                parts = section.split('\n## ', 1)
                if len(parts) > 1:
                    section = '## ' + parts[1]  # Mantener el ## al inicio
                else:
                    continue  # No hay FAQs en esta sección
            
            # Buscar secciones que empiecen con ##
            if not section.startswith('##'):
                continue
            
            faq_counter += 1
            
            # Extraer título (## Título)
            title_match = re.search(r'##\s+(.+)', section)
            if not title_match:
                continue
            
            title = title_match.group(1).strip()
            
            # Extraer contenido (texto entre título y metadatos)
            # Primero intentar con metadatos
            content_match = re.search(r'##.+?\n\n(.+?)\n\n\*\*', section, re.DOTALL)
            if not content_match:
                # Si no hay metadatos, tomar todo después del título hasta el final
                content_match = re.search(r'##.+?\n\n(.+?)(?:\n\n\*\*|\Z)', section, re.DOTALL)
            
            if not content_match:
                logger.warning(f"No se pudo extraer contenido de: {title}")
                continue
            
            text = content_match.group(1).strip()
            
            # Extraer metadatos (opcional)
            category_match = re.search(r'\*\*Categoría\*\*:\s*(.+)', section)
            topic_match = re.search(r'\*\*Tema\*\*:\s*(.+)', section)
            
            category = category_match.group(1).strip() if category_match else "general"
            topic = topic_match.group(1).strip() if topic_match else "general"
            
            # Combinar título y contenido para mejor búsqueda semántica
            # Esto ayuda a que el RAG encuentre el contenido cuando se pregunta por el título
            full_text = f"{title}\n\n{text}"
            
            logger.info(f"Parseado FAQ #{faq_counter}: {title} | Categoría: {category}")
            
            faqs.append({
                "id": f"faq_{faq_counter}",
                "title": title,
                "text": full_text,  # Ahora incluye el título
                "metadata": {
                    "category": category,
                    "topic": topic,
                    "title": title
                }
            })
        
        return faqs
        
    except Exception as e:
        logger.error(f"Error parseando archivo markdown: {e}", exc_info=True)
        return []


def _load_sample_data():
    """Carga datos desde archivo markdown en ChromaDB"""
    # Ruta al archivo de FAQs
    markdown_path = Path(__file__).parent.parent.parent / "data" / "faqs_cootradecun.md"
    
    if not markdown_path.exists():
        logger.warning(f"Archivo de FAQs no encontrado: {markdown_path}")
        logger.warning("Creando datos de ejemplo básicos...")
        # Fallback a datos básicos
        sample_faqs = [{
            "id": "faq_1",
            "text": "Cootradecun es una cooperativa de trabajadores de Cundinamarca.",
            "metadata": {"category": "general", "topic": "info"}
        }]
    else:
        # Parsear el archivo markdown
        sample_faqs = _parse_markdown_faqs(markdown_path)
        logger.info(f"✅ Parseados {len(sample_faqs)} FAQs desde {markdown_path.name}")
    
    if not sample_faqs:
        logger.error("No se pudieron cargar FAQs")
        return
    
    # Insertar en ChromaDB
    collection.add(
        ids=[faq["id"] for faq in sample_faqs],
        documents=[faq["text"] for faq in sample_faqs],
        metadatas=[faq["metadata"] for faq in sample_faqs]
    )
    
    logger.info(f"✅ Cargados {len(sample_faqs)} documentos en ChromaDB")
    
    # Log de los títulos cargados para debug
    for faq in sample_faqs:
        logger.debug(f"   - {faq['id']}: {faq['title']} ({faq['metadata']['category']})")


@tool("rag_search")
def rag_search(query: str, top_k: int = 5) -> Dict:
    """
    Busca información relevante en la base de conocimiento de Cootradecun.
    
    Args:
        query: La pregunta o consulta del usuario
        top_k: Número de resultados a retornar (por defecto 5)
    
    Returns:
        Dict con la respuesta y las fuentes consultadas
    """
    try:
        if collection is None:
            initialize_rag()
        
        logger.info(f"🔍 RAG search: '{query}' (buscando top {top_k} resultados)")
        
        # Realizar búsqueda semántica
        results = collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        if not results["documents"] or not results["documents"][0]:
            logger.warning(f"❌ No se encontraron documentos para: '{query}'")
            return {
                "answer": "No encontré información específica sobre tu consulta en nuestra base de conocimiento.",
                "sources": [],
                "found": False
            }
        
        # Construir respuesta con los resultados más relevantes
        passages = results["documents"][0]
        sources = results["ids"][0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0] if "distances" in results else []
        
        # Log de resultados encontrados
        logger.info(f"✅ Encontrados {len(passages)} resultados:")
        for i, (source_id, metadata) in enumerate(zip(sources, metadatas)):
            title = metadata.get("title", "Sin título") if metadata else "Sin título"
            distance = distances[i] if i < len(distances) else "N/A"
            logger.info(f"   {i+1}. {source_id}: {title} (distancia: {distance})")
        
        # Tomar el pasaje más relevante como respuesta principal
        answer = passages[0] if passages else "No encontré información relevante."
        
        # Si hay múltiples resultados relevantes, combinarlos
        if len(passages) > 1:
            # Opcional: combinar los primeros 2 resultados si son muy relevantes
            logger.debug(f"Usando resultado principal: {sources[0]}")
        
        return {
            "answer": answer,
            "sources": sources,
            "all_passages": passages,
            "found": True,
            "metadata": metadatas[0] if metadatas else {}
        }
        
    except Exception as e:
        logger.error(f"❌ Error en rag_search: {e}", exc_info=True)
        return {
            "answer": f"Ocurrió un error al buscar información: {str(e)}",
            "sources": [],
            "found": False
        }

