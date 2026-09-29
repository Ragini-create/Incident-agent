import os
import json
from pathlib import Path
from dotenv import load_dotenv
import psycopg
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

knowledge_base = [
    {
        "content": "Auth Service 504 Gateway Timeouts: Triggered by Redis cache evictions or token refresh lock contention. Remediation: Flush expired token blacklist in Redis or restart auth pod replicas.",
        "metadata": {"service": "auth", "category": "runbook"}
    },
    {
        "content": "Database High Latency: When replica CPU exceeds 80%, kill idle transactions and inspect query locks using pg_stat_activity before failing over.",
        "metadata": {"service": "database", "category": "runbook"}
    },
    {
        "content": "Payment Gateway Glitches: Verify Stripe webhook idempotency keys. If failure persists beyond 5 minutes, reroute traffic to the Adyen backup provider.",
        "metadata": {"service": "payments", "category": "runbook"}
    }
]


def get_embeddings_model():
    return GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2-preview",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        task_type="RETRIEVAL_DOCUMENT",
        output_dimensionality=768
    )


def seed(db_uri: str | None = None, embeddings_inst=None):
    if not db_uri:
        db_uri = os.getenv("DATABASE_URL")
    if not db_uri:
        raise ValueError("DATABASE_URL is not set.")

    if embeddings_inst is None:
        embeddings_inst = get_embeddings_model()

    print("Connecting to Supabase Postgres database...")
    with psycopg.connect(db_uri, connect_timeout=15, prepare_threshold=None) as conn:
        with conn.cursor() as cur:
            # Query existing runbooks for idempotency check
            cur.execute("SELECT metadata->>'service' as service, content FROM incident_docs;")
            existing_rows = cur.fetchall()
            existing_set = {(r[0], r[1]) for r in existing_rows}

            to_insert = [
                doc for doc in knowledge_base
                if (doc["metadata"].get("service"), doc["content"]) not in existing_set
            ]

            if not to_insert:
                print("All runbook documents are already seeded. Skipping generation.")
                return 0

            print(f"Generating Gemini embeddings for {len(to_insert)} new document(s)...")
            texts = [doc["content"] for doc in to_insert]
            vectors = embeddings_inst.embed_documents(texts)

            for doc, vec in zip(to_insert, vectors):
                vec_str = f"[{','.join(str(x) for x in vec)}]"
                cur.execute(
                    """
                    INSERT INTO incident_docs (content, metadata, embedding)
                    VALUES (%s, %s, %s::vector)
                    ON CONFLICT ((metadata->>'service'), content) DO NOTHING;
                    """,
                    (doc["content"], json.dumps(doc["metadata"]), vec_str)
                )
        conn.commit()

    print(f"Success! Seeded {len(to_insert)} new document(s) into Supabase incident_docs.")
    return len(to_insert)


if __name__ == "__main__":
    seed()