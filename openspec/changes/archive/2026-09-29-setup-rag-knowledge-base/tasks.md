# Tasks

## 1. Migration & Database Schema Setup

- [x] 1.1 Create `migrations/001_create_incident_docs.sql` containing the `incident_docs` table DDL (768-dim vector, JSONB metadata, unique constraint on service and content), HNSW vector index, and `match_incident_docs` RPC function supporting service-based metadata filtering. Verify SQL file syntax and completeness.

## 2. Idempotent Knowledge Base Seeding

- [x] 2.1 Refactor `seed_rag.py` to embed sample runbooks (auth 504 timeouts, database high latency, payment gateway failures) with 768-dim Gemini embeddings and check existing database records before insertion to guarantee idempotent seeding. Verify running `seed_rag.py` twice consecutively does not generate duplicate records.

## 3. Automated Unit & Integration Testing

- [x] 3.1 Create `tests/test_rag.py` containing unit and integration tests with mocked Gemini embeddings and mocked PostgreSQL database connections, verifying cosine search execution, metadata filter handling, and seeding idempotency offline via `pytest tests/test_rag.py`.
