-- LangGraph Checkpoint Tables for PostgreSQL
-- Uses public schema (default) to avoid search_path issues

-- Drop existing tables if any issues
DROP TABLE IF EXISTS public.checkpoint_writes CASCADE;
DROP TABLE IF EXISTS public.checkpoint_blobs CASCADE;
DROP TABLE IF EXISTS public.checkpoints CASCADE;
DROP TABLE IF EXISTS public.checkpoint_migrations CASCADE;

-- Migration tracking table
CREATE TABLE public.checkpoint_migrations (
    v INTEGER PRIMARY KEY
);

-- Main checkpoints table with proper PRIMARY KEY
CREATE TABLE public.checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint JSONB NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

-- Checkpoint blobs table
CREATE TABLE public.checkpoint_blobs (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    channel TEXT NOT NULL,
    version TEXT NOT NULL,
    type TEXT NOT NULL,
    blob BYTEA,
    PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
);

-- Checkpoint writes table with proper PRIMARY KEY
CREATE TABLE public.checkpoint_writes (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    task_path TEXT NOT NULL DEFAULT '',
    idx INTEGER NOT NULL,
    channel TEXT NOT NULL,
    type TEXT,
    blob BYTEA NOT NULL,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, task_path, idx)
);

-- Create index for performance
CREATE INDEX IF NOT EXISTS checkpoint_writes_thread_idx 
ON public.checkpoint_writes(thread_id);

-- Record all migrations as applied
INSERT INTO public.checkpoint_migrations (v) 
VALUES (1), (2), (3), (4), (5), (6)
ON CONFLICT (v) DO NOTHING;
