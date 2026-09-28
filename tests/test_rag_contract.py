"""RAG/API/provider contracts without a running model or production DB writes."""

import importlib.util
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from rag.chain import RAGChain
from llm.factory import create_llm_provider
from vectorstore.chroma_store import ChromaVectorStore


class RAGContractTests(unittest.TestCase):
    def make_chain(self):
        rag = RAGChain.__new__(RAGChain)
        rag.top_k = 3
        rag.embedder = Mock()
        rag.embedder.embed_text.return_value = [1.0, 0.0]
        rag.llm = Mock()
        rag.llm.generate.return_value = "06:42"
        rag.vector_store = Mock()
        rag.vector_store.search.return_value = {"ids": [[]], "distances": [[]]}
        rag.vector_store.get_all_documents.return_value = {
            "ids": ["actual-chunk-id"], "documents": ["Departure* 06:42"],
            "metadatas": [{"source": "new-upload.pdf", "page": "2", "document_id": "upload-1"}],
        }
        return rag

    def test_answer_context_and_citations_share_actual_metadata(self):
        rag = self.make_chain()
        result = rag.ask("  When is the train departing?  ")
        self.assertEqual(result["question"], "When is the train departing?")
        self.assertEqual(result["citations"], [{"source": "new-upload.pdf", "page": 3}])
        self.assertEqual(result["results"]["ids"], [["actual-chunk-id"]])
        self.assertIn("Departure* 06:42", rag.llm.generate.call_args.kwargs["user_prompt"])
        self.assertIn("new-upload.pdf, page 3", result["context"])
        rag.embedder.embed_text.assert_called_once_with(result["question"])

    def test_empty_question_is_rejected_before_embedding(self):
        rag = self.make_chain()
        with self.assertRaises(ValueError):
            rag.ask("  ")
        rag.embedder.embed_text.assert_not_called()

    def test_exact_passenger_answer_keeps_citations_without_model_guessing(self):
        rag = self.make_chain()
        rag.vector_store.get_all_documents.return_value["documents"] = [
            "# Name Age Gender Booking Status Current Status\n"
            "1. B KUMAR 32 M CNF/C3/19/WINDOW   CNF/C3/19/WINDOW\nPayment Details\nINR 650.00"
        ]
        result = rag.ask("List passenger details")
        self.assertIn("Name: B KUMAR", result["answer"])
        self.assertIn("Seat/berth: 19", result["answer"])
        self.assertNotIn("650.00", result["answer"])
        self.assertEqual(result["citations"], [{"source": "new-upload.pdf", "page": 3}])
        self.assertIn("650.00", result["results"]["documents"][0][0])
        rag.llm.generate.assert_not_called()

    def test_new_upload_is_visible_without_restart(self):
        rag = self.make_chain()
        rag.retrieve("Departure?")
        rag.vector_store.get_all_documents.return_value = {
            "ids": ["second-upload"], "documents": ["Arrival: 21:09"],
            "metadatas": [{"source": "second.pdf", "page": "0"}],
        }
        self.assertEqual(rag.retrieve("Arrival?")["ids"], [["second-upload"]])

    def test_fastapi_contract(self):
        from fastapi.testclient import TestClient
        rag = self.make_chain()
        spec = importlib.util.spec_from_file_location("nexora_test_api", ROOT / "ai-service/api.py")
        api = importlib.util.module_from_spec(spec)
        with patch("rag.chain.RAGChain", return_value=rag):
            spec.loader.exec_module(api)
        with TestClient(api.app) as client:
            self.assertEqual(client.get("/health").status_code, 200)
            rag.vector_store.get_statistics.return_value = {
                "total_chunks": 7,
                "indexed_documents": 2,
                "documents": [{"document_id": "uploaded", "source": "manual.pdf", "chunks": 4}],
            }
            stats = client.get("/stats")
            self.assertEqual(stats.status_code, 200)
            self.assertEqual(stats.json()["total_chunks"], 7)
            self.assertEqual(stats.json()["documents"][0]["source"], "manual.pdf")
            response = client.post("/ask", json={"question": "When is the train departing?"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(set(response.json()), {"question", "answer", "citations"})
            self.assertEqual(response.json()["citations"][0]["page"], 3)
            self.assertEqual(client.post("/ask", json={"question": " "}).status_code, 400)
            self.assertEqual(client.post("/ask", json={}).status_code, 422)
            with patch.object(api, "index_document", return_value={
                "filename": "company_faq.txt", "documents": 1, "chunks": 1, "vectors": 1,
            }) as index:
                response = client.post("/index", json={
                    "file_path": str(ROOT / "data/sample_documents/company_faq.txt"),
                    "document_id": "fresh-upload",
                })
                self.assertEqual(response.status_code, 200)
                self.assertEqual(index.call_args.kwargs["document_id"], "fresh-upload")

    def test_provider_selection_preserved(self):
        for name, constructor in [("ollama", "OllamaLLM"), ("nvidia", "NVIDIACloudLLM")]:
            with self.subTest(provider=name), patch.dict(os.environ, {"LLM_PROVIDER": name}), patch("llm.factory." + constructor) as provider:
                self.assertIs(create_llm_provider(), provider.return_value)
        with patch.dict(os.environ, {"LLM_PROVIDER": "invalid"}):
            with self.assertRaises(ValueError):
                create_llm_provider()

    def test_vector_search_limit_empty_and_ids(self):
        store = ChromaVectorStore.__new__(ChromaVectorStore)
        store.collection = Mock()
        store.collection.count.return_value = 0
        self.assertEqual(store.search([1.0])["ids"], [[]])
        store.collection.query.assert_not_called()
        store.collection.count.return_value = 24
        store.search([1.0], n_results=7)
        self.assertEqual(store.collection.query.call_args.kwargs["n_results"], 7)
        store.search([1.0], n_results=100)
        self.assertEqual(store.collection.query.call_args.kwargs["n_results"], 24)

    def test_chroma_statistics_group_actual_chunk_metadata(self):
        store = ChromaVectorStore.__new__(ChromaVectorStore)
        store.get_all_documents = Mock(return_value={
            "ids": ["a", "b", "c"],
            "metadatas": [
                {"document_id": "upload-a", "source": "manual.pdf"},
                {"document_id": "upload-a", "source": "manual.pdf"},
                {"document_id": "upload-b", "source": "faq.txt"},
            ],
        })

        self.assertEqual(store.get_statistics(), {
            "total_chunks": 3,
            "indexed_documents": 2,
            "documents": [
                {"document_id": "upload-b", "source": "faq.txt", "chunks": 1},
                {"document_id": "upload-a", "source": "manual.pdf", "chunks": 2},
            ],
        })


if __name__ == "__main__":
    unittest.main()
