# Proposal

## Why

The autonomous incident triage agent requires a persistent vector store to search internal remediation runbooks by semantic similarity during incident investigations. Currently, the knowledge base seeding script (`seed_rag.py`) lacks idempotency, metadata filtering functions, formal database migration definitions, and comprehensive test coverage. Establishing a robust RAG knowledge base setup using Supabase `pgvector` ensures reliable, idempotent runbook ingestion and cosine similarity retrieval without interfering with agent checkpoint state.

## What Changes

- Create a SQL migration for Supabase `pgvector` defining the `incident_docs` table with columns for runbook content, JSON metadata, and 768-dimensional vector embeddings.
- Add an idempotent index (`hnsw` or `ivfflat`) on `incident_docs.embedding` for cosine distance calculations.
- Create a PostgreSQL RPC function `match_incident_docs` supporting cosine similarity search with optional JSON metadata filtering (e.g., filtering by service name).
- Refactor `seed_rag.py` to seed three core runbooks (auth 504 timeouts, database high latency, payment gateway failures) idempotently by checking existing content/metadata signatures before insertion.
- Add suite of unit/integration tests (`tests/test_rag.py`) mocking Gemini embedding calls and database connections to ensure independent testability.
- Preserve existing LangGraph checkpointer tables (`checkpoints`, `checkpoint_blobs`, `checkpoint_writes`) without schema modifications.

## Capabilities

### New Capabilities
- `rag-knowledge-base`: Stores system runbook documents with 768-dim embeddings in Supabase pgvector and provides metadata-filtered cosine similarity matching and idempotent database seeding.

### Modified Capabilities
(None)

## Impact

- **Database**: Adds `incident_docs` table and `match_incident_docs` RPC function to Supabase Postgres schema. Checkpoint tables remain unchanged.
- **Scripts**: Updates `seed_rag.py` for idempotent document upsert/skip logic.
- **Tests**: Adds unit tests under `tests/test_rag.py` using `unittest.mock` / `pytest` for embedding and database calls.
- **Dependencies**: Uses existing `langchain-google-genai` and `psycopg[binary,pool]` packages.
