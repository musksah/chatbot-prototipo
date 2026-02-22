"""
RAG Module — Advanced Retrieval from pgvector (PostgreSQL).

Implements:
1. Hybrid Search: cosine similarity (vector) + full-text search (BM25/tsvector)
   fused via Reciprocal Rank Fusion (RRF)
2. Parent Chunk Expansion: retrieves child chunks for precision, returns
   parent chunks for richer LLM context (Small-to-Big Retrieval)
3. Re-Ranking: uses Gemini to re-order chunks by actual relevance
4. Connection Pooling: lazy ConnectionPool instead of per-query connections
5. Contextual Output: includes source, page, and similarity in returned text
"""

import os
import logging
from typing import Optional

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)

# --- Configuration ---
DATABASE_URL = os.getenv("DATABASE_URL")
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# Retrieval parameters
DEFAULT_K = 4              # Final number of chunks returned to LLM
HYBRID_K_VECTOR = 8        # Candidates from vector search
HYBRID_K_FTS = 8           # Candidates from full-text search
MIN_SIMILARITY = 0.25      # Minimum cosine similarity threshold
RERANK_CANDIDATES = 8      # Chunks sent to re-ranker
ENABLE_RERANK = True       # Toggle re-ranking (disable for lower latency)
ENABLE_PARENT_EXPANSION = True  # Toggle parent chunk expansion

# Department → document title mapping
DEPT_TO_TITLE = {
    "atencion_asociado": "Atención al Asociado",
    "nominas": "Nóminas",
    "vivienda": "Vivienda",
    "convenios": "Convenios",
    "cartera": "Cartera",
    "contabilidad": "Contabilidad",
    "tesoreria": "Tesorería",
    "credito": "Crédito",
}

# --- Connection Pool (lazy) ---
_pool: Optional[ConnectionPool] = None


def _get_pool() -> ConnectionPool:
    """Lazy-initialize a connection pool for pgvector queries."""
    global _pool
    if _pool is None:
        if not DATABASE_URL:
            raise RuntimeError("RAG: DATABASE_URL not configured")
        _pool = ConnectionPool(
            conninfo=DATABASE_URL,
            min_size=1,
            max_size=5,
            max_lifetime=3600,
            reconnect_timeout=30,
        )
    return _pool


# --- Hybrid Search SQL ---
HYBRID_SEARCH_SQL = """
WITH vector_results AS (
    SELECT c.id, c.content, c.parent_chunk_id, c.page_number, c.is_parent,
           1 - (c.embedding <=> %(query_vector)s::vector) AS vec_score,
           ROW_NUMBER() OVER (ORDER BY c.embedding <=> %(query_vector)s::vector) AS vec_rank
    FROM rag_chunk c
    JOIN rag_document d ON c.document_id = d.id
    WHERE d.title = %(title)s AND d.status = 'indexed'
      AND (c.is_parent = FALSE OR c.is_parent IS NULL)
    ORDER BY c.embedding <=> %(query_vector)s::vector
    LIMIT %(k_vector)s
),
fts_results AS (
    SELECT c.id, c.content, c.parent_chunk_id, c.page_number, c.is_parent,
           ts_rank(c.content_tsvector, plainto_tsquery('spanish', %(query_text)s)) AS fts_score,
           ROW_NUMBER() OVER (
               ORDER BY ts_rank(c.content_tsvector, plainto_tsquery('spanish', %(query_text)s)) DESC
           ) AS fts_rank
    FROM rag_chunk c
    JOIN rag_document d ON c.document_id = d.id
    WHERE d.title = %(title)s AND d.status = 'indexed'
      AND c.content_tsvector @@ plainto_tsquery('spanish', %(query_text)s)
      AND (c.is_parent = FALSE OR c.is_parent IS NULL)
    LIMIT %(k_fts)s
),
combined AS (
    SELECT 
        COALESCE(v.id, f.id) AS id,
        COALESCE(v.content, f.content) AS content,
        COALESCE(v.parent_chunk_id, f.parent_chunk_id) AS parent_chunk_id,
        COALESCE(v.page_number, f.page_number) AS page_number,
        COALESCE(v.vec_score, 0) AS vec_score,
        COALESCE(f.fts_score, 0) AS fts_score,
        -- Reciprocal Rank Fusion (k=60 is standard)
        COALESCE(1.0 / (60 + v.vec_rank), 0) + COALESCE(1.0 / (60 + f.fts_rank), 0) AS rrf_score
    FROM vector_results v
    FULL OUTER JOIN fts_results f 
        ON v.id = f.id
)
SELECT id, content, parent_chunk_id, page_number, vec_score, fts_score, rrf_score
FROM combined
WHERE vec_score >= %(min_similarity)s OR fts_score > 0
ORDER BY rrf_score DESC
LIMIT %(k)s
"""

# --- Parent Chunk Lookup SQL ---
PARENT_CHUNK_SQL = """
SELECT content FROM rag_chunk WHERE id = %s AND is_parent = TRUE
"""


def _hybrid_search(query: str, department: str, k: int = RERANK_CANDIDATES) -> list[dict]:
    """
    Hybrid search: vector cosine similarity + BM25 full-text search.
    Returns top-k candidate chunks with scores.
    """
    pool = _get_pool()
    
    # Generate query embedding
    query_vector = embeddings.embed_query(query)
    query_vector_str = str(query_vector)
    
    title = DEPT_TO_TITLE.get(department, department)
    
    with pool.connection() as conn:
        results = conn.execute(
            HYBRID_SEARCH_SQL,
            {
                "query_vector": query_vector_str,
                "query_text": query,
                "title": title,
                "k_vector": HYBRID_K_VECTOR,
                "k_fts": HYBRID_K_FTS,
                "min_similarity": MIN_SIMILARITY,
                "k": k,
            }
        ).fetchall()
        
        chunks = []
        for row in results:
            chunk = {
                "id": row[0],
                "content": row[1],
                "parent_chunk_id": row[2],
                "page_number": row[3],
                "vec_score": float(row[4]),
                "fts_score": float(row[5]),
                "rrf_score": float(row[6]),
            }
            chunks.append(chunk)
        
        # Expand parent chunks if enabled
        if ENABLE_PARENT_EXPANSION:
            for chunk in chunks:
                if chunk["parent_chunk_id"]:
                    parent = conn.execute(
                        PARENT_CHUNK_SQL, (str(chunk["parent_chunk_id"]),)
                    ).fetchone()
                    if parent:
                        chunk["content"] = parent[0]  # Use parent's richer content
    
    # Log search statistics
    vec_hits = sum(1 for c in chunks if c["vec_score"] > 0)
    fts_hits = sum(1 for c in chunks if c["fts_score"] > 0)
    both_hits = sum(1 for c in chunks if c["vec_score"] > 0 and c["fts_score"] > 0)
    logger.info(
        f"📚 [HYBRID] {department}: query='{query[:50]}...', "
        f"results={len(chunks)} (vec={vec_hits}, fts={fts_hits}, both={both_hits})"
    )
    
    return chunks


def _rerank_chunks(query: str, chunks: list[dict], top_k: int = DEFAULT_K) -> list[dict]:
    """
    Re-rank chunks using Gemini as a cross-encoder.
    Sends the query + chunk contents to Gemini and asks it to rank by relevance.
    """
    if not chunks:
        return []
    
    if len(chunks) <= top_k:
        return chunks  # No need to re-rank if fewer than top_k
    
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
        
        numbered_chunks = "\n\n".join([
            f"[{i+1}] {c['content'][:500]}" for i, c in enumerate(chunks)
        ])
        
        prompt = (
            f"Eres un evaluador de relevancia para un chatbot de COOTRADECUN (cooperativa colombiana). "
            f"Dada la pregunta del usuario y los fragmentos de documentos, selecciona los {top_k} "
            f"fragmentos MÁS relevantes para responder la pregunta.\n\n"
            f"Pregunta: {query}\n\n"
            f"Fragmentos:\n{numbered_chunks}\n\n"
            f"Responde SOLO con los números de los {top_k} fragmentos más relevantes, "
            f"ordenados de mayor a menor relevancia, separados por comas. "
            f"Ejemplo: 3,1,5,2"
        )
        
        result = llm.invoke(prompt)
        response_text = result.content.strip()
        
        # Parse the ranking
        indices = []
        for part in response_text.replace(" ", "").split(","):
            try:
                idx = int(part) - 1  # Convert 1-indexed to 0-indexed
                if 0 <= idx < len(chunks):
                    indices.append(idx)
            except ValueError:
                continue
        
        if indices:
            reranked = [chunks[i] for i in indices[:top_k]]
            logger.info(
                f"📊 [RERANK] Reordered {len(chunks)} → {len(reranked)} chunks. "
                f"Order: {[i+1 for i in indices[:top_k]]}"
            )
            return reranked
        else:
            logger.warning(f"📊 [RERANK] Could not parse ranking: '{response_text}'. Using original order.")
            return chunks[:top_k]
    
    except Exception as e:
        logger.warning(f"📊 [RERANK] Error during re-ranking: {e}. Using original order.")
        return chunks[:top_k]


def _format_output(chunks: list[dict], department: str) -> str:
    """Format chunks with source attribution for the LLM."""
    if not chunks:
        return "No se encontró información relevante."
    
    formatted = []
    for chunk in chunks:
        page = chunk.get("page_number")
        vec = chunk.get("vec_score", 0)
        fts = chunk.get("fts_score", 0)
        
        header_parts = [f"Fuente: {DEPT_TO_TITLE.get(department, department)}"]
        if page is not None:
            header_parts.append(f"Pág. {page + 1}")
        if vec > 0:
            header_parts.append(f"Sim: {vec:.2f}")
        
        header = f"[{', '.join(header_parts)}]"
        formatted.append(f"{header}\n{chunk['content']}")
    
    return "\n\n---\n\n".join(formatted)


def search_by_department(query: str, department: str, k: int = DEFAULT_K) -> str:
    """
    Advanced RAG search pipeline:
    1. Hybrid search (vector + BM25) → get RERANK_CANDIDATES chunks
    2. Re-rank with Gemini → keep top k
    3. Format with source attribution
    
    Returns formatted context string for the LLM agent.
    """
    try:
        # Step 1: Hybrid search
        candidates = _hybrid_search(query, department, k=RERANK_CANDIDATES)
        
        if not candidates:
            logger.info(f"📚 [RAG] {department}: query='{query[:50]}...', chunks=0 (no results)")
            return "No se encontró información relevante."
        
        # Step 2: Re-rank (if enabled)
        if ENABLE_RERANK and len(candidates) > k:
            final_chunks = _rerank_chunks(query, candidates, top_k=k)
        else:
            final_chunks = candidates[:k]
        
        # Step 3: Format output
        result = _format_output(final_chunks, department)
        
        # Log final stats
        total_chars = sum(len(c["content"]) for c in final_chunks)
        avg_sim = sum(c["vec_score"] for c in final_chunks) / len(final_chunks)
        logger.info(
            f"📚 [RAG] {department}: query='{query[:50]}...', "
            f"final_chunks={len(final_chunks)}, total_chars={total_chars}, "
            f"avg_similarity={avg_sim:.3f}"
        )
        
        return result
    
    except Exception as e:
        logger.error(f"RAG: Error querying {department}: {e}")
        return f"Error retrieving information: {e}"


def _invoke_retriever_with_logging(retriever_name: str, query: str, k: int = DEFAULT_K) -> str:
    """
    Public API used by tools.py.
    Wraps search_by_department for backward compatibility.
    """
    return search_by_department(query=query, department=retriever_name, k=k)
