-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create incident_docs table for RAG runbooks
CREATE TABLE IF NOT EXISTS incident_docs (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding VECTOR(768),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_doc_service_content UNIQUE ((metadata->>'service'), content)
);

-- Index for fast cosine similarity search
CREATE INDEX IF NOT EXISTS idx_incident_docs_embedding 
ON incident_docs USING hnsw (embedding vector_cosine_ops);

-- Stored function for cosine similarity matching with optional metadata filtering
CREATE OR REPLACE FUNCTION match_incident_docs(
    query_embedding VECTOR(768),
    match_threshold FLOAT DEFAULT 0.0,
    match_count INT DEFAULT 5,
    filter_service TEXT DEFAULT NULL
)
RETURNS TABLE (
    id BIGINT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        incident_docs.id,
        incident_docs.content,
        incident_docs.metadata,
        (1 - (incident_docs.embedding <=> query_embedding))::FLOAT AS similarity
    FROM incident_docs
    WHERE (1 - (incident_docs.embedding <=> query_embedding)) >= match_threshold
      AND (filter_service IS NULL OR filter_service = '' OR incident_docs.metadata->>'service' = filter_service)
    ORDER BY incident_docs.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
