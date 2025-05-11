-- schema.sql
-- SQL schema for setting up the PGVector table for the Supagrok Contextual RAG Pipeline.
-- PRF-DIRECTIVE: PRF-CONTEXTUAL-RAG-SUPPORT-ARTIFACTS-2025-05-08-A

-- Ensure the pgvector extension is available.
-- This might require superuser privileges to execute for the first time in a database.
CREATE EXTENSION IF NOT EXISTS vector;

-- Table to store document chunks and their embeddings.
CREATE TABLE IF NOT EXISTS document_embeddings (
    id UUID PRIMARY KEY,                      -- Unique identifier for each chunk embedding
    file_uuid UUID NOT NULL,                  -- UUID of the original source file this chunk belongs to
    chunk_text TEXT NOT NULL,                 -- The actual text content of the chunk
    embedding VECTOR(1536) NOT NULL,          -- Vector embedding of the chunk_text (1536 dimensions for OpenAI text-embedding-ada-002)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP -- Timestamp of when the record was created
);

-- Optional: Create an index for faster similarity searches on the embedding_vector.
-- The type of index (e.g., HNSW, IVFFlat) and its parameters depend on the dataset size and query patterns.
-- Example for IVFFlat (adjust lists and probes as needed):
-- CREATE INDEX ON document_embeddings USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);
-- Example for HNSW (adjust m and ef_construction as needed):
-- CREATE INDEX ON document_embeddings USING hnsw (embedding vector_l2_ops);

COMMENT ON TABLE document_embeddings IS 'Stores text chunks from documents and their corresponding vector embeddings for similarity search.';
COMMENT ON COLUMN document_embeddings.id IS 'Primary key, unique UUID for the embedding record.';
COMMENT ON COLUMN document_embeddings.file_uuid IS 'UUID of the source document from which this chunk was extracted.';
COMMENT ON COLUMN document_embeddings.chunk_text IS 'The text content of the document chunk.';
COMMENT ON COLUMN document_embeddings.embedding IS 'Vector representation of the chunk_text, dimension 1536 for OpenAI text-embedding-ada-002.';
COMMENT ON COLUMN document_embeddings.created_at IS 'Timestamp indicating when the embedding record was inserted.';
