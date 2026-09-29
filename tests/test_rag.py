import os
import json
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

from seed_rag import seed, knowledge_base
from agent import search_remediation_runbooks


class TestRAGKnowledgeBase(unittest.TestCase):

    def test_sql_migration_file_exists_and_valid(self):
        migration_path = Path(__file__).resolve().parent.parent / "migrations" / "001_create_incident_docs.sql"
        self.assertTrue(migration_path.exists(), "Migration SQL file must exist.")

        sql_content = migration_path.read_text(encoding="utf-8")
        self.assertIn("CREATE TABLE IF NOT EXISTS incident_docs", sql_content)
        self.assertIn("VECTOR(768)", sql_content)
        self.assertIn("idx_incident_docs_embedding", sql_content)
        self.assertIn("match_incident_docs", sql_content)
        self.assertIn("filter_service", sql_content)

    @patch("seed_rag.psycopg.connect")
    def test_seed_initial_inserts_all_documents(self, mock_connect):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        # Simulate empty database table
        mock_cur.fetchall.return_value = []

        # Mock embeddings instance
        mock_embeddings = MagicMock()
        mock_embeddings.embed_documents.return_value = [
            [0.1] * 768,
            [0.2] * 768,
            [0.3] * 768,
        ]

        seeded_count = seed(db_uri="postgresql://mock:mock@localhost:5432/mockdb", embeddings_inst=mock_embeddings)

        self.assertEqual(seeded_count, len(knowledge_base))
        mock_embeddings.embed_documents.assert_called_once()
        self.assertEqual(mock_cur.execute.call_count, 1 + len(knowledge_base))  # 1 SELECT + N INSERTs

    @patch("seed_rag.psycopg.connect")
    def test_seed_idempotent_skips_existing_documents(self, mock_connect):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        # Simulate existing documents in database
        mock_cur.fetchall.return_value = [
            (doc["metadata"]["service"], doc["content"]) for doc in knowledge_base
        ]

        mock_embeddings = MagicMock()

        seeded_count = seed(db_uri="postgresql://mock:mock@localhost:5432/mockdb", embeddings_inst=mock_embeddings)

        self.assertEqual(seeded_count, 0)
        mock_embeddings.embed_documents.assert_not_called()

    @patch("agent.pool.connection")
    @patch("agent.rag_embeddings")
    def test_search_remediation_runbooks_tool_success(self, mock_rag_embeddings, mock_connection):
        mock_rag_embeddings.embed_query.return_value = [0.05] * 768

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        mock_cur.fetchall.return_value = [
            ("auth", "Auth Service 504 Gateway Timeouts remediation steps.", 0.89),
            ("database", "Database High Latency remediation steps.", 0.82),
        ]

        result = search_remediation_runbooks.invoke({"query": "auth timeout"})
        self.assertIn("[auth]: Auth Service 504 Gateway Timeouts remediation steps.", result)
        self.assertIn("[database]: Database High Latency remediation steps.", result)

    @patch("agent.pool.connection")
    @patch("agent.rag_embeddings")
    def test_search_remediation_runbooks_tool_no_results(self, mock_rag_embeddings, mock_connection):
        mock_rag_embeddings.embed_query.return_value = [0.05] * 768

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        mock_cur.fetchall.return_value = []

        result = search_remediation_runbooks.invoke({"query": "unknown service issue"})
        self.assertEqual(result, "No relevant runbooks found.")


if __name__ == "__main__":
    unittest.main()
