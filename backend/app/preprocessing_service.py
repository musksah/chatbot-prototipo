"""
RAG Preprocessing Service — Text Cleaning & Enrichment Pipeline

Processes raw PDF text through 6 stages before chunking:
  1. Text Cleaning (regex)
  2. Unicode Normalization
  3. Header/Footer Removal
  4. LLM Contextual Enrichment (post-chunking)
  5. Quality Gate (post-chunking)
  6. Near-Duplicate Detection (post-chunking)

Usage:
    # Pre-chunking: clean raw pages
    cleaned_pages = preprocess_pages(pages)

    # Post-chunking: filter, enrich, deduplicate
    chunks = quality_gate(chunks)
    chunks = deduplicate_chunks(chunks)
    chunks = enrich_chunks_with_context(chunks, document_title)
"""

import re
import logging
import unicodedata
from collections import Counter
from typing import Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# Stage 1 — Text Cleaning
# ═══════════════════════════════════════════════════════════════════════

def _clean_text(text: str) -> str:
    """
    Remove PDF extraction artifacts from text.

    Fixes:
      - Multiple spaces between words (common in PDF column extraction)
      - Excessive newlines
      - Control characters
      - Orphaned bullet points and page markers
    """
    if not text:
        return ""

    # Remove control characters (keep \n and \t)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # Collapse runs of spaces (but not newlines) into a single space
    text = re.sub(r'[^\S\n]+', ' ', text)

    # Collapse 3+ consecutive newlines into 2 (preserve paragraph breaks)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Remove lines that are only whitespace
    text = re.sub(r'\n[ \t]+\n', '\n\n', text)

    # Remove isolated page number lines: "  3  " or "Pág. 12"
    text = re.sub(r'\n\s*(?:Pág\.?\s*\d+|pág\.?\s*\d+|\d{1,3})\s*\n', '\n', text)

    # Remove orphan bullet artifacts: lines of just "•", "-", "·"
    text = re.sub(r'\n\s*[•\-·]\s*\n', '\n', text)

    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)

    # Final trim
    return text.strip()


# ═══════════════════════════════════════════════════════════════════════
# Stage 2 — Unicode Normalization
# ═══════════════════════════════════════════════════════════════════════

def _normalize_unicode(text: str) -> str:
    """
    Normalize Unicode for consistent search and embedding.

    Fixes:
      - Fullwidth characters (Ａ → A)
      - Ligatures (ﬁ → fi)
      - Soft hyphens, zero-width characters
      - Smart quotes → standard quotes
    """
    if not text:
        return ""

    # NFKC: decomposes compatibility characters, then recomposes
    # This handles fullwidth, ligatures, superscripts, etc.
    text = unicodedata.normalize('NFKC', text)

    # Remove soft hyphens (invisible but break FTS matching)
    text = text.replace('\u00ad', '')

    # Remove zero-width characters
    text = re.sub(r'[\u200b\u200c\u200d\ufeff\u200e\u200f]', '', text)

    # Normalize dash variants → standard hyphen
    text = re.sub(r'[\u2010\u2011\u2012\u2013\u2014\u2015]', '-', text)

    # Normalize quotes
    text = text.replace('\u201c', '"').replace('\u201d', '"')  # " "
    text = text.replace('\u2018', "'").replace('\u2019', "'")  # ' '
    text = text.replace('\u00ab', '"').replace('\u00bb', '"')  # « »

    # Normalize ellipsis
    text = text.replace('\u2026', '...')

    return text


# ═══════════════════════════════════════════════════════════════════════
# Stage 3 — Header/Footer Detection & Removal
# ═══════════════════════════════════════════════════════════════════════

def _detect_repeated_patterns(pages: list[dict], min_occurrence_ratio: float = 0.5) -> list[str]:
    """
    Detect text patterns that repeat across multiple pages (likely headers/footers).

    Strategy: Extract first and last 2 lines of each page, find patterns
    that appear in >50% of pages.
    """
    if len(pages) < 3:
        return []  # Not enough pages to detect patterns

    # Collect first/last lines from each page
    edge_lines: list[str] = []
    for page in pages:
        lines = [l.strip() for l in page["content"].split('\n') if l.strip()]
        if lines:
            edge_lines.extend(lines[:2])   # First 2 lines
            edge_lines.extend(lines[-2:])  # Last 2 lines

    # Count occurrences, ignoring page numbers (normalize digits)
    normalized_counts: Counter[str] = Counter()
    pattern_map: dict[str, str] = {}  # normalized → original

    for line in edge_lines:
        # Normalize: replace digits with # to detect "Page 1", "Page 2", etc.
        normalized = re.sub(r'\d+', '#', line).strip()
        if len(normalized) < 5:
            continue  # Too short to be meaningful
        normalized_counts[normalized] += 1
        pattern_map[normalized] = line

    # Keep patterns that appear in more than min_occurrence_ratio of pages
    threshold = len(pages) * min_occurrence_ratio
    repeated = [
        normalized
        for normalized, count in normalized_counts.items()
        if count >= threshold
    ]

    if repeated:
        logger.info(f"  🔍 Detected {len(repeated)} repeating header/footer patterns")

    return repeated


def _remove_headers_footers(text: str, patterns: list[str]) -> str:
    """Remove lines matching detected header/footer patterns."""
    if not patterns:
        return text

    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        normalized_line = re.sub(r'\d+', '#', line).strip()
        if normalized_line in patterns:
            continue  # Skip this header/footer line
        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


# ═══════════════════════════════════════════════════════════════════════
# Stage 4 — LLM Contextual Enrichment (post-chunking)
# ═══════════════════════════════════════════════════════════════════════

def enrich_chunks_with_context(
    chunks: list[dict],
    document_title: str,
    model_name: str = "gemini-2.5-flash",
) -> list[dict]:
    """
    Use Gemini to prepend a short contextual label to each chunk.

    This significantly improves embedding quality by adding semantic context
    that would otherwise be lost during chunking.

    Example:
      Before: "Desprendible de pago, Doc. de identidad..."
      After:  "[Crédito > Requisitos > Documentación] Desprendible de pago..."
    """
    from langchain_google_genai import ChatGoogleGenerativeAI

    if not chunks:
        return chunks

    llm = ChatGoogleGenerativeAI(model=model_name, temperature=0)

    # Process in batches to reduce API calls
    BATCH_SIZE = 10
    enriched = []
    total_batches = (len(chunks) - 1) // BATCH_SIZE + 1

    for batch_idx in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[batch_idx:batch_idx + BATCH_SIZE]

        # Build a single prompt with all chunks in the batch
        chunks_text = ""
        for i, chunk in enumerate(batch):
            preview = chunk["content"][:300]
            chunks_text += f"\n---CHUNK {i}---\n{preview}\n"

        prompt = (
            f"Eres un clasificador de contenido para documentos de COOTRADECUN "
            f"(una cooperativa colombiana).\n\n"
            f"Documento: \"{document_title}\"\n\n"
            f"Para cada chunk abajo, genera UNA etiqueta corta en formato "
            f"[Categoría > Subcategoría] que describa su contenido.\n"
            f"La etiqueta debe ser máximo 6 palabras.\n"
            f"Responde SOLO con las etiquetas, una por línea, en el formato:\n"
            f"0: [etiqueta]\n"
            f"1: [etiqueta]\n"
            f"...\n\n"
            f"Chunks:{chunks_text}"
        )

        try:
            response = llm.invoke(prompt)
            labels = _parse_enrichment_labels(response.content, len(batch))

            for chunk, label in zip(batch, labels):
                if label:
                    chunk["content"] = f"{label} {chunk['content']}"
                    # Update preview too
                    chunk["content_preview"] = chunk["content"][:200]
                enriched.append(chunk)

        except Exception as e:
            logger.warning(f"  ⚠️ Enrichment failed for batch {batch_idx // BATCH_SIZE + 1}: {e}")
            # Fall back: use chunks without enrichment
            enriched.extend(batch)

        logger.info(
            f"  ✨ Enriched batch {batch_idx // BATCH_SIZE + 1}/{total_batches}"
        )

    return enriched


def _parse_enrichment_labels(response_text: str, expected_count: int) -> list[str]:
    """Parse LLM response into labels list."""
    labels = [""] * expected_count

    for line in response_text.strip().split('\n'):
        line = line.strip()
        match = re.match(r'(\d+)\s*:\s*(.+)', line)
        if match:
            idx = int(match.group(1))
            label = match.group(2).strip()
            if 0 <= idx < expected_count:
                labels[idx] = label

    return labels


# ═══════════════════════════════════════════════════════════════════════
# Stage 5 — Quality Gate (post-chunking)
# ═══════════════════════════════════════════════════════════════════════

MIN_CHUNK_LENGTH = 50        # Characters
MAX_NUMERIC_RATIO = 0.80     # >80% digits/symbols = junk


def quality_gate(chunks: list[dict]) -> list[dict]:
    """
    Filter out low-quality chunks that would pollute the RAG index.

    Filters:
      - Too short (< 50 chars)
      - Mostly numeric/symbols (> 80%)
      - Empty or whitespace-only
    """
    if not chunks:
        return chunks

    passed = []
    discarded = 0

    for chunk in chunks:
        content = chunk["content"].strip()

        # Filter: empty
        if not content:
            discarded += 1
            continue

        # Filter: too short
        if len(content) < MIN_CHUNK_LENGTH:
            discarded += 1
            continue

        # Filter: mostly numeric/symbols
        alpha_count = sum(1 for c in content if c.isalpha())
        total_count = len(content)
        if total_count > 0 and (alpha_count / total_count) < (1 - MAX_NUMERIC_RATIO):
            discarded += 1
            continue

        passed.append(chunk)

    if discarded:
        logger.info(f"  🚫 Quality gate: discarded {discarded} low-quality chunks")

    return passed


# ═══════════════════════════════════════════════════════════════════════
# Stage 6 — Near-Duplicate Detection (post-chunking)
# ═══════════════════════════════════════════════════════════════════════

SHINGLE_SIZE = 5            # Character n-gram size for shingling
SIMILARITY_THRESHOLD = 0.90  # Jaccard similarity threshold


def _shingle(text: str, k: int = SHINGLE_SIZE) -> set[str]:
    """Create a set of character-level k-shingles from text."""
    text = text.lower().strip()
    if len(text) < k:
        return {text}
    return {text[i:i + k] for i in range(len(text) - k + 1)}


def _jaccard_similarity(set_a: set, set_b: set) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union else 0.0


def deduplicate_chunks(chunks: list[dict]) -> list[dict]:
    """
    Remove near-duplicate chunks using character shingling + Jaccard similarity.

    Keeps the first occurrence, removes subsequent near-duplicates (>90% similar).
    """
    if len(chunks) <= 1:
        return chunks

    # Pre-compute shingles
    shingles = [_shingle(c["content"]) for c in chunks]

    keep_mask = [True] * len(chunks)
    removed = 0

    for i in range(len(chunks)):
        if not keep_mask[i]:
            continue
        for j in range(i + 1, len(chunks)):
            if not keep_mask[j]:
                continue
            sim = _jaccard_similarity(shingles[i], shingles[j])
            if sim >= SIMILARITY_THRESHOLD:
                keep_mask[j] = False
                removed += 1

    result = [c for c, keep in zip(chunks, keep_mask) if keep]

    if removed:
        logger.info(f"  🔄 Deduplication: removed {removed} near-duplicate chunks")

    return result


# ═══════════════════════════════════════════════════════════════════════
# PUBLIC API — Main entry point (pre-chunking)
# ═══════════════════════════════════════════════════════════════════════

def preprocess_pages(
    pages: list[dict],
    remove_headers: bool = True,
) -> list[dict]:
    """
    Apply all pre-chunking preprocessing stages to raw PDF pages.

    Args:
        pages: List of {"content": str, "page_number": int} from PDF reader
        remove_headers: Whether to detect and remove repeating headers/footers

    Returns:
        Cleaned pages with same structure, ready for chunking.
    """
    if not pages:
        return pages

    original_chars = sum(len(p["content"]) for p in pages)

    # Stage 3: Detect repeated patterns BEFORE cleaning individual pages
    repeated_patterns: list[str] = []
    if remove_headers and len(pages) >= 3:
        repeated_patterns = _detect_repeated_patterns(pages)

    cleaned_pages = []
    for page in pages:
        text = page["content"]

        # Stage 1: Text cleaning
        text = _clean_text(text)

        # Stage 2: Unicode normalization
        text = _normalize_unicode(text)

        # Stage 3: Remove headers/footers
        if repeated_patterns:
            text = _remove_headers_footers(text, repeated_patterns)

        # Keep page if it has meaningful content
        if text.strip():
            cleaned_pages.append({
                "content": text,
                "page_number": page["page_number"],
            })

    cleaned_chars = sum(len(p["content"]) for p in cleaned_pages)
    reduction = ((original_chars - cleaned_chars) / original_chars * 100) if original_chars else 0

    logger.info(
        f"  🧹 Preprocessing: {original_chars:,} → {cleaned_chars:,} chars "
        f"({reduction:.1f}% noise removed), "
        f"{len(pages)} → {len(cleaned_pages)} pages"
    )

    return cleaned_pages
