"""
Script de Indexación Offline para RAG con pgvector.

Procesa los PDFs del directorio docs/, genera embeddings con Gemini,
y los guarda en las tablas rag_document + rag_chunk de PostgreSQL.

V2: Semantic chunking with parent-child strategy (Small-to-Big Retrieval).
    Parent chunks (1500 chars) provide context.
    Child chunks (400 chars) are used for retrieval precision.
    tsvector is auto-populated by DB trigger.

Uso:
    python script_index.py          # Indexa todos los PDFs
    python script_index.py --reset  # Borra datos existentes y re-indexa
"""

import os
import re
import sys
import uuid
import logging
import psycopg
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Config ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment.")

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
embeddings_model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

FILES_CONFIG = [
    ("atencion al asociado.pdf", "Atención al Asociado", "atencion_asociado"),
    ("nominas.pdf", "Nóminas", "nominas"),
    ("vivienda.pdf", "Vivienda", "vivienda"),
    ("convenios.pdf", "Convenios", "convenios"),
    ("cartera.pdf", "Cartera", "cartera"),
    ("contabilidad.pdf", "Contabilidad", "contabilidad"),
    ("tesoreria.pdf", "Tesorería", "tesoreria"),
    ("credito.pdf", "Crédito", "credito"),
]

# --- Chunking Configuration (synced with dashboard's indexing_service.py) ---
PARENT_CHUNK_SIZE = 1500
PARENT_CHUNK_OVERLAP = 200
CHILD_CHUNK_SIZE = 400
CHILD_CHUNK_OVERLAP = 50
SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " "]
EMBEDDING_BATCH_SIZE = 20

parent_splitter = RecursiveCharacterTextSplitter(
    chunk_size=PARENT_CHUNK_SIZE,
    chunk_overlap=PARENT_CHUNK_OVERLAP,
    separators=SEPARATORS,
)

child_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHILD_CHUNK_SIZE,
    chunk_overlap=CHILD_CHUNK_OVERLAP,
    separators=SEPARATORS,
)


def _estimate_page_number(content: str, pages: list[dict]) -> int | None:
    """Estimate which page a chunk came from by checking content overlap."""
    snippet = content[:100]
    for page in pages:
        if snippet in page["content"]:
            return page["page_number"]
    return None


def create_parent_child_chunks(pages: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Create parent and child chunks from PDF pages.
    
    Parent chunks (~1500 chars): provide richer context to LLM.
    Child chunks (~400 chars): used for similarity matching.
    Each child references its parent.
    
    Returns: (parent_chunks, child_chunks)
    """
    full_text = "\n\n".join([p["content"] for p in pages])
    
    parent_docs = parent_splitter.split_documents([Document(page_content=full_text)])
    
    parent_chunks = []
    child_chunks = []
    
    for p_idx, parent_doc in enumerate(parent_docs):
        parent_content = parent_doc.page_content.strip()
        if not parent_content:
            continue
        
        parent_chunks.append({
            "content": parent_content,
            "chunk_index": p_idx,
            "page_number": _estimate_page_number(parent_content, pages),
            "is_parent": True,
            "parent_index": None,
        })
        
        child_docs = child_splitter.split_documents([Document(page_content=parent_content)])
        
        for c_idx, child_doc in enumerate(child_docs):
            child_content = child_doc.page_content.strip()
            if not child_content:
                continue
            child_chunks.append({
                "content": child_content,
                "chunk_index": len(parent_chunks) + len(child_chunks) - 1,
                "page_number": _estimate_page_number(child_content, pages),
                "is_parent": False,
                "parent_index": p_idx,
            })
    
    return parent_chunks, child_chunks


def split_vivienda_by_project(docs) -> tuple[list[dict], list[dict]]:
    """Custom splitter for vivienda.pdf: extract projects, then create parent/child chunks."""
    logger.info("  Splitting vivienda docs into project chunks")
    full_text = "\n".join([doc.page_content for doc in docs])
    full_text = re.sub(r'\s+', ' ', full_text)

    project_patterns = [
        (r'1\.\s*EL\s*PEDREGAL.*?(?=2\.\s*RANCHO\s*GRANDE|$)', 'EL PEDREGAL - FUSAGASUGÁ'),
        (r'2\.\s*RANCHO\s*GRANDE.*?(?=3\.\s*ARRAYANES|$)', 'RANCHO GRANDE - MELGAR'),
        (r'3\.\s*ARRAYANES.*', 'ARRAYANES DE PEÑALISA II - RICAURTE'),
    ]

    pages = []
    for pattern, project_name in project_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE | re.DOTALL)
        if match:
            content = f"[PROYECTO: {project_name}]\n\n{match.group(0).strip()}"
            pages.append({"content": content, "page_number": None})
            logger.info(f"    Extracted project '{project_name}' ({len(content)} chars)")

    if not pages:
        logger.warning("    Project split failed, using pages from PDF directly")
        pages = [{"content": doc.page_content, "page_number": doc.metadata.get("page", 0)} for doc in docs]

    return create_parent_child_chunks(pages)


def process_and_index(reset: bool = False):
    """Main indexing function with parent-child chunking."""
    logger.info("=" * 60)
    logger.info("Starting RAG Offline Indexer (v2 — Semantic Chunking)")
    logger.info(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")
    logger.info(f"Docs dir: {DOCS_DIR}")
    logger.info(f"Parent chunks: {PARENT_CHUNK_SIZE} chars | Child chunks: {CHILD_CHUNK_SIZE} chars")
    logger.info("=" * 60)

    conn = psycopg.connect(DATABASE_URL)
    conn.autocommit = True

    if reset:
        logger.warning("RESET MODE: Deleting all existing RAG data...")
        conn.execute("DELETE FROM rag_chunk")
        conn.execute("DELETE FROM rag_document")
        logger.info("All RAG data deleted.")

    total_parents = 0
    total_children = 0

    for filename, title, department in FILES_CONFIG:
        filepath = os.path.join(DOCS_DIR, filename)
        if not os.path.exists(filepath):
            logger.warning(f"File not found, skipping: {filename}")
            continue

        # Check if already indexed
        result = conn.execute(
            "SELECT id FROM rag_document WHERE file_name = %s AND status = 'indexed'",
            (filename,)
        ).fetchone()
        if result and not reset:
            logger.info(f"Already indexed: {filename} — skipping (use --reset to re-index)")
            continue

        logger.info(f"Processing: {filename} (title: {title})")

        # Insert document record
        doc_id = str(uuid.uuid4())
        file_size = os.path.getsize(filepath)
        conn.execute(
            """INSERT INTO rag_document (id, title, file_name, file_type, file_size_bytes, status, total_chunks)
               VALUES (%s, %s, %s, 'pdf', %s, 'processing', 0)""",
            (doc_id, title, filename, file_size)
        )

        try:
            # Load PDF
            loader = PyPDFLoader(filepath)
            docs = loader.load()
            logger.info(f"  Loaded {len(docs)} pages from PDF")

            # Create parent/child chunks
            if department == "vivienda":
                parent_chunks, child_chunks = split_vivienda_by_project(docs)
            else:
                pages = [{"content": d.page_content, "page_number": d.metadata.get("page", 0)} for d in docs]
                parent_chunks, child_chunks = create_parent_child_chunks(pages)

            all_chunks = parent_chunks + child_chunks
            logger.info(
                f"  Created {len(parent_chunks)} parent + {len(child_chunks)} child "
                f"= {len(all_chunks)} total chunks"
            )

            # Generate embeddings in batches
            logger.info(f"  Generating embeddings for {len(all_chunks)} chunks...")
            all_texts = [c["content"] for c in all_chunks]
            all_embeddings = []

            for i in range(0, len(all_texts), EMBEDDING_BATCH_SIZE):
                batch = all_texts[i:i + EMBEDDING_BATCH_SIZE]
                vectors = embeddings_model.embed_documents(batch)
                all_embeddings.extend(vectors)
                logger.info(
                    f"  Embedded batch {i // EMBEDDING_BATCH_SIZE + 1}/"
                    f"{(len(all_texts) - 1) // EMBEDDING_BATCH_SIZE + 1}"
                )

            # Insert parent chunks first
            parent_ids = {}
            for i, (chunk, embedding) in enumerate(
                zip(parent_chunks, all_embeddings[:len(parent_chunks)])
            ):
                chunk_id = str(uuid.uuid4())
                parent_ids[chunk["chunk_index"]] = chunk_id

                preview = chunk["content"][:200]
                token_count = len(chunk["content"].split())

                conn.execute(
                    """INSERT INTO rag_chunk 
                       (id, document_id, chunk_index, content, content_preview, 
                        embedding, page_number, token_count, is_parent, parent_chunk_id)
                       VALUES (%s, %s, %s, %s, %s, %s::vector, %s, %s, TRUE, NULL)""",
                    (chunk_id, doc_id, chunk["chunk_index"],
                     chunk["content"], preview, str(embedding),
                     chunk.get("page_number"), token_count)
                )

            # Insert child chunks with parent reference
            child_embeddings = all_embeddings[len(parent_chunks):]
            for chunk, embedding in zip(child_chunks, child_embeddings):
                chunk_id = str(uuid.uuid4())
                parent_db_id = parent_ids.get(
                    parent_chunks[chunk["parent_index"]]["chunk_index"]
                )

                preview = chunk["content"][:200]
                token_count = len(chunk["content"].split())

                conn.execute(
                    """INSERT INTO rag_chunk 
                       (id, document_id, chunk_index, content, content_preview, 
                        embedding, page_number, token_count, is_parent, parent_chunk_id)
                       VALUES (%s, %s, %s, %s, %s, %s::vector, %s, %s, FALSE, %s)""",
                    (chunk_id, doc_id, chunk["chunk_index"],
                     chunk["content"], preview, str(embedding),
                     chunk.get("page_number"), token_count, parent_db_id)
                )

            # Update document status
            total = len(parent_chunks) + len(child_chunks)
            conn.execute(
                "UPDATE rag_document SET status = 'indexed', total_chunks = %s WHERE id = %s",
                (total, doc_id)
            )
            total_parents += len(parent_chunks)
            total_children += len(child_chunks)
            logger.info(f"  ✅ {filename}: {len(parent_chunks)} parents + {len(child_chunks)} children indexed")

        except Exception as e:
            logger.error(f"  ❌ Error processing {filename}: {e}")
            conn.execute(
                "UPDATE rag_document SET status = 'error', error_message = %s WHERE id = %s",
                (str(e), doc_id)
            )

    conn.close()
    logger.info("=" * 60)
    logger.info(f"Indexing complete! Parents: {total_parents}, Children: {total_children}, "
                f"Total: {total_parents + total_children}")
    logger.info("=" * 60)


if __name__ == "__main__":
    reset_mode = "--reset" in sys.argv
    process_and_index(reset=reset_mode)
