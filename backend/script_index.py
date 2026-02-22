"""
Script de Indexación Offline para RAG con pgvector.

Procesa los PDFs del directorio docs/, genera embeddings con Gemini,
y los guarda en las tablas rag_document + rag_chunk de PostgreSQL.

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


def split_vivienda_by_project(docs):
    """Custom splitter for vivienda.pdf that keeps each project together."""
    logger.info("Splitting vivienda docs into project chunks")
    full_text = "\n".join([doc.page_content for doc in docs])
    full_text = re.sub(r'\s+', ' ', full_text)

    project_patterns = [
        (r'1\.\s*EL\s*PEDREGAL.*?(?=2\.\s*RANCHO\s*GRANDE|$)', 'EL PEDREGAL - FUSAGASUGÁ'),
        (r'2\.\s*RANCHO\s*GRANDE.*?(?=3\.\s*ARRAYANES|$)', 'RANCHO GRANDE - MELGAR'),
        (r'3\.\s*ARRAYANES.*', 'ARRAYANES DE PEÑALISA II - RICAURTE'),
    ]

    project_docs = []
    for pattern, project_name in project_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE | re.DOTALL)
        if match:
            content = f"[PROYECTO: {project_name}]\n\n{match.group(0).strip()}"
            project_docs.append({"content": content, "page_number": None})
            logger.info(f"  Extracted project '{project_name}' ({len(content)} chars)")

    if not project_docs:
        logger.warning("  Project split failed, falling back to large chunks")
        splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=500)
        splits = splitter.split_documents(docs)
        project_docs = [{"content": s.page_content, "page_number": s.metadata.get("page")} for s in splits]

    return project_docs


def process_and_index(reset: bool = False):
    """Main indexing function."""
    logger.info("=" * 60)
    logger.info("Starting RAG Offline Indexer")
    logger.info(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")
    logger.info(f"Docs dir: {DOCS_DIR}")
    logger.info("=" * 60)

    conn = psycopg.connect(DATABASE_URL)
    conn.autocommit = True

    if reset:
        logger.warning("RESET MODE: Deleting all existing RAG data...")
        conn.execute("DELETE FROM rag_chunk")
        conn.execute("DELETE FROM rag_document")
        logger.info("All RAG data deleted.")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    total_chunks = 0

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

        logger.info(f"Processing: {filename} (department: {department})")

        # Insert document record
        doc_id = str(uuid.uuid4())
        file_size = os.path.getsize(filepath)
        conn.execute(
            """INSERT INTO rag_document (id, title, file_name, file_type, file_size_bytes, status, total_chunks)
               VALUES (%s, %s, %s, 'pdf', %s, 'processing', 0)""",
            (doc_id, title, filename, file_size)
        )

        try:
            # Load and split
            loader = PyPDFLoader(filepath)
            docs = loader.load()

            if department == "vivienda":
                chunks = split_vivienda_by_project(docs)
            else:
                splits = text_splitter.split_documents(docs)
                chunks = [{"content": s.page_content, "page_number": s.metadata.get("page")} for s in splits]

            logger.info(f"  Created {len(chunks)} chunks. Generating embeddings...")

            # Generate embeddings in batches
            batch_size = 20
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                texts = [c["content"] for c in batch]
                vectors = embeddings_model.embed_documents(texts)

                for j, (chunk, vector) in enumerate(zip(batch, vectors)):
                    chunk_index = i + j
                    preview = chunk["content"][:200] if len(chunk["content"]) > 200 else chunk["content"]
                    token_count = len(chunk["content"].split())

                    conn.execute(
                        """INSERT INTO rag_chunk (document_id, chunk_index, content, content_preview, embedding, page_number, token_count)
                           VALUES (%s, %s, %s, %s, %s::vector, %s, %s)""",
                        (doc_id, chunk_index, chunk["content"], preview, str(vector), chunk.get("page_number"), token_count)
                    )

                logger.info(f"  Batch {i // batch_size + 1}/{(len(chunks) - 1) // batch_size + 1} uploaded")

            # Update document status
            conn.execute(
                "UPDATE rag_document SET status = 'indexed', total_chunks = %s WHERE id = %s",
                (len(chunks), doc_id)
            )
            total_chunks += len(chunks)
            logger.info(f"  ✅ {filename}: {len(chunks)} chunks indexed")

        except Exception as e:
            logger.error(f"  ❌ Error processing {filename}: {e}")
            conn.execute(
                "UPDATE rag_document SET status = 'error', error_message = %s WHERE id = %s",
                (str(e), doc_id)
            )

    conn.close()
    logger.info("=" * 60)
    logger.info(f"Indexing complete! Total new chunks: {total_chunks}")
    logger.info("=" * 60)


if __name__ == "__main__":
    reset_mode = "--reset" in sys.argv
    process_and_index(reset=reset_mode)
