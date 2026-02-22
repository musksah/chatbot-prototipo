"""
RAG Module — Retrieval from pgvector (PostgreSQL).

Queries the existing rag_document + rag_chunk tables in corvus_dashboard.
Uses cosine similarity search with optional department filtering.
"""

import os
import logging
import psycopg
from langchain_google_genai import GoogleGenerativeAIEmbeddings

logger = logging.getLogger(__name__)

# Initialize embeddings model (same as indexer)
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

DATABASE_URL = os.getenv("DATABASE_URL")

# Connection pool (lazy)
_pool = None


def _get_connection():
    """Get a database connection. Uses a simple connection for now."""
    if not DATABASE_URL:
        logger.error("RAG: DATABASE_URL not configured.")
        return None
    try:
        return psycopg.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"RAG: Failed to connect to database: {e}")
        return None


def search_by_department(query: str, department: str, k: int = 4) -> str:
    """
    Searches rag_chunk table using cosine similarity, filtered by department.
    
    The department filter works by joining rag_chunk → rag_document → matching title.
    """
    conn = _get_connection()
    if not conn:
        return "No information available. Database connection failed."

    try:
        # Generate embedding for the query
        query_vector = embeddings.embed_query(query)
        query_vector_str = str(query_vector)

        # Map department names to document titles
        dept_to_title = {
            "atencion_asociado": "Atención al Asociado",
            "nominas": "Nóminas",
            "vivienda": "Vivienda",
            "convenios": "Convenios",
            "cartera": "Cartera",
            "contabilidad": "Contabilidad",
            "tesoreria": "Tesorería",
            "credito": "Crédito",
        }
        title = dept_to_title.get(department, department)

        # Cosine similarity search filtered by document title
        results = conn.execute(
            """
            SELECT c.content, c.chunk_index, c.page_number,
                   1 - (c.embedding <=> %s::vector) AS similarity
            FROM rag_chunk c
            JOIN rag_document d ON c.document_id = d.id
            WHERE d.title = %s AND d.status = 'indexed'
            ORDER BY c.embedding <=> %s::vector
            LIMIT %s
            """,
            (query_vector_str, title, query_vector_str, k)
        ).fetchall()

        if not results:
            logger.info(f"📚 [RAG] {department}: query='{query[:50]}...', chunks=0 (no results)")
            return "No se encontró información relevante."

        # Log statistics
        chunks_count = len(results)
        total_chars = sum(len(r[0]) for r in results)
        avg_similarity = sum(r[3] for r in results) / chunks_count
        logger.info(
            f"📚 [RAG] {department}: query='{query[:50]}...', "
            f"chunks={chunks_count}, total_chars={total_chars}, "
            f"avg_similarity={avg_similarity:.3f}"
        )

        return "\n\n".join([r[0] for r in results])

    except Exception as e:
        logger.error(f"RAG: Error querying {department}: {e}")
        return f"Error retrieving information: {e}"
    finally:
        conn.close()


def _invoke_retriever_with_logging(retriever_name: str, query: str, k: int = 4) -> str:
    """
    Public API used by tools.py.
    Wraps search_by_department for backward compatibility.
    """
    return search_by_department(query=query, department=retriever_name, k=k)
