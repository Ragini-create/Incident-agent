# Spec Delta

## Purpose

Provides storage, embedding generation, similarity retrieval, and idempotent seeding for internal system remediation runbooks using Supabase pgvector and Gemini embeddings.

## ADDED Requirements

### Requirement: Supabase pgvector Runbook Storage Schema
The system SHALL store incident remediation runbooks in a dedicated Supabase PostgreSQL table named `incident_docs` containing runbook content, JSON metadata, and 768-dimensional vector embeddings generated using Gemini embeddings.

#### Scenario: Insert runbook document into pgvector table
- **WHEN** a runbook document with text content, JSON metadata, and a 768-element floating-point vector is inserted
- **THEN** the system stores the content, metadata, and vector embedding in the `incident_docs` table successfully

### Requirement: Cosine Similarity Vector Matching with Metadata Filter
The database SHALL provide a `match_incident_docs` stored function (RPC) that computes cosine distance similarity (`<=>`) between a query embedding vector and stored runbooks, returning the top matching documents with optional JSON metadata filtering by service.

#### Scenario: Similarity search with service filter
- **WHEN** a client calls `match_incident_docs` with a query vector, a similarity threshold, a match limit, and a service name filter
- **THEN** the database returns only matching runbook rows belonging to that specified service sorted by highest similarity score

#### Scenario: Similarity search without metadata filter
- **WHEN** a client calls `match_incident_docs` with a query vector, a match limit, and a null or empty service filter
- **THEN** the database returns top matching runbooks across all services sorted by similarity score

### Requirement: Idempotent Runbook Knowledge Base Seeding
The seeding utility `seed_rag.py` SHALL seed sample remediation runbooks covering Auth 504 Gateway Timeouts, Database High Latency, and Payment Gateway Glitches into `incident_docs`, ensuring that running the script multiple times does not insert duplicate rows.

#### Scenario: Initial seeding execution
- **WHEN** `seed_rag.py` is executed against an empty `incident_docs` table
- **THEN** three distinct runbooks (auth, database, payments) are embedded using Gemini and stored in the database

#### Scenario: Subsequent seeding execution
- **WHEN** `seed_rag.py` is executed again against an already seeded `incident_docs` table
- **THEN** existing runbook entries are recognized by unique metadata or content comparison and no duplicate records are inserted

### Requirement: LangGraph Checkpoint State Isolation
The system SHALL maintain complete schema and operational isolation between `incident_docs` and LangGraph checkpoint tables (`checkpoints`, `checkpoint_blobs`, `checkpoint_writes`), ensuring RAG setup operations leave existing agent state untouched.

#### Scenario: Seeding or querying RAG database
- **WHEN** RAG database migrations, seeding, or vector queries are executed
- **THEN** existing LangGraph checkpoint tables remain unchanged in structure and content

### Requirement: RAG Capability Unit and Integration Testing
The RAG subsystem SHALL include unit and integration tests under `tests/test_rag.py` that mock external Gemini API calls and database connections to enable fast, offline, and reliable verification.

#### Scenario: Running test suite offline
- **WHEN** `pytest` or `python -m unittest` is executed for `tests/test_rag.py`
- **THEN** tests pass using mocked embedding vectors and mocked database connections without making external API calls or database mutations
