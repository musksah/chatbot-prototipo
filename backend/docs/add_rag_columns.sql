-- ============================================================
-- Advanced RAG Migration — Add columns for Hybrid Search
-- 
-- Run this ONCE on the corvus_dashboard database before
-- deploying the updated chatbot/dashboard code.
--
-- Safe to re-run (uses IF NOT EXISTS / IF EXISTS checks).
-- ============================================================

-- 1. Full-text search column (tsvector for BM25-style keyword search)
ALTER TABLE rag_chunk ADD COLUMN IF NOT EXISTS content_tsvector tsvector;

-- GIN index for fast full-text search
CREATE INDEX IF NOT EXISTS idx_rag_chunk_fts ON rag_chunk USING gin(content_tsvector);

-- 2. Parent-child chunk relationships (Small-to-Big Retrieval)
--    parent_chunk_id links a child chunk to its larger parent chunk.
--    is_parent marks chunks that are parents (returned for context, not for matching).
ALTER TABLE rag_chunk ADD COLUMN IF NOT EXISTS parent_chunk_id UUID;
ALTER TABLE rag_chunk ADD COLUMN IF NOT EXISTS is_parent BOOLEAN DEFAULT FALSE;

-- Add FK constraint only if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_rag_chunk_parent' 
        AND table_name = 'rag_chunk'
    ) THEN
        ALTER TABLE rag_chunk 
            ADD CONSTRAINT fk_rag_chunk_parent 
            FOREIGN KEY (parent_chunk_id) REFERENCES rag_chunk(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Index for quick parent lookup
CREATE INDEX IF NOT EXISTS idx_rag_chunk_parent ON rag_chunk(parent_chunk_id) WHERE parent_chunk_id IS NOT NULL;

-- 3. Populate tsvector for existing data (Spanish config)
UPDATE rag_chunk SET content_tsvector = to_tsvector('spanish', content)
WHERE content_tsvector IS NULL;

-- 4. Create trigger to auto-populate tsvector on INSERT/UPDATE
CREATE OR REPLACE FUNCTION rag_chunk_tsvector_trigger()
RETURNS TRIGGER AS $$
BEGIN
    NEW.content_tsvector := to_tsvector('spanish', COALESCE(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_rag_chunk_tsvector ON rag_chunk;
CREATE TRIGGER trg_rag_chunk_tsvector
    BEFORE INSERT OR UPDATE OF content ON rag_chunk
    FOR EACH ROW
    EXECUTE FUNCTION rag_chunk_tsvector_trigger();
