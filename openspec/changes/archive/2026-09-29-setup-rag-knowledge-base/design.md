# Design

## Context

The Incident Triage Agent relies on Supabase Postgres for both vector similarity search over runbooks and graph checkpoint persistence.
Existing connection pooling uses `psycopg_pool.ConnectionPool` with `autocommit=True` and `prepare_threshold=None` to avoid transaction pooler issues on Supabase (PgBouncer mode).

See `proposal.md` for background and high-level requirements.

## Goals / Non-Goals

**Goals:**
- Provide a versioned SQL migration script for `incident_docs` and `match_incident_docs` RPC function.
- Support 768-dimensional Gemini vector embeddings (`gemini-embedding-2-preview` / `text-embedding-004`).
- Implement cosine similarity search with optional JSON metadata filtering by service.
- Refactor `seed_rag.py` to make seeding idempotent and quota-efficient.
- Add comprehensive mock-backed unit and integration tests under `tests/`.

**Non-Goals:**
- Modifying LangGraph state graphs (`agent.py`).
- Changing FastAPI routes or Gradio interface UI (`app.py`).
- Altering existing checkpoint database tables (`checkpoints`, `checkpoint_blobs`, `checkpoint_writes`).

## Decisions

### Decision 1: SQL Migration and RPC Function (`migrations/001_create_incident_docs.sql`)
**Choice:** Store DDL and RPC helper in a dedicated migration file.
- Table Schema:
  - `id`: `BIGSERIAL PRIMARY KEY`
  - `content`: `TEXT NOT NULL`
  - `metadata`: `JSONB DEFAULT '{}'::jsonb`
  - `embedding`: `VECTOR(768)`
  - Unique Constraint: `CONSTRAINT unique_doc_service_content UNIQUE ((metadata->>'service'), content)` to enable idempotent upserts.
- Indexing: `CREATE INDEX IF NOT EXISTS idx_incident_docs_embedding ON incident_docs USING hnsw (embedding vector_cosine_ops);`
- RPC Stored Function: `match_incident_docs(query_embedding vector(768), match_threshold float, match_count int, filter_service text)` returning similarity scored rows.

*Alternatives Considered:* In-line table creation in Python code (rejected: harder to track database schema evolution across environments).

### Decision 2: Idempotent Seeding Strategy in `seed_rag.py`
**Choice:** Check database state for existing `service` + `content` combinations *before* calling Gemini embedding APIs.
- Flow:
  1. Connect to database pool.
  2. Query existing documents matching metadata and content.
  3. Filter out already-existing documents.
  4. Generate Gemini embeddings *only* for missing documents.
  5. Perform SQL upsert/insert for new documents.

*Rationale:* Prevents redundant Gemini API rate consumption on repeated script runs and guarantees zero duplicate runbook entries.

### Decision 3: Testing Architecture (`tests/test_rag.py`)
**Choice:** Use `unittest.mock` to patch `GoogleGenerativeAIEmbeddings.embed_query` and `embed_documents`, as well as `psycopg` connection pools.
- Unit Tests: Test embedding format validation, SQL query string formatting, and metadata filter handling.
- Integration Tests (Mocked DB): Test `search_remediation_runbooks` tool output parsing and fallback handling when no runbooks are returned.

## Risks / Trade-offs

- **[Risk] Supabase PgBouncer Transaction Mode Error**: Prepared statement failures if default driver settings are used.
  - **Mitigation**: Maintain `prepare_threshold=None` in all psycopg connection kwargs across helper scripts and tools.
- **[Risk] Dimension Mismatch**: Embedding API default dimensions (e.g. 1536 or 3072) vs 768d vector column.
  - **Mitigation**: Explicitly specify `output_dimensionality=768` on `GoogleGenerativeAIEmbeddings` instances.
- **[Risk] Gemini API Quota Limits during test execution**: API calls failing during offline CI/CD or local test runs.
  - **Mitigation**: Fully mock embedding calls in unit tests so test suite runs offline without API keys.

## Migration Plan

1. Execute `migrations/001_create_incident_docs.sql` against Supabase database.
2. Run `python seed_rag.py` to seed sample runbooks.
3. Run `pytest tests/` to confirm test suite passes.
4. Rollback Plan: `DROP TABLE IF EXISTS incident_docs CASCADE; DROP FUNCTION IF EXISTS match_incident_docs;`.
