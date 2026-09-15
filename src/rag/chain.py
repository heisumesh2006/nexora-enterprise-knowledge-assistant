import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from dotenv import load_dotenv

from embeddings.embedder import DocumentEmbedder
from llm.factory import create_llm_provider
from vectorstore.chroma_store import ChromaVectorStore


load_dotenv()


class RAGChain:
    """
    Retrieval-Augmented Generation pipeline for the Nexora
    Enterprise Knowledge Assistant.
    """

    def __init__(
        self,
        top_k: int = 3,
        collection_name: str = "nexora_documents",
    ):
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")

        self.top_k = top_k

        self.embedder = DocumentEmbedder()

        self.vector_store = ChromaVectorStore(
            persist_directory=PROJECT_ROOT / "data" / "chroma",
            collection_name=collection_name,
        )

        self.llm = create_llm_provider()

    def retrieve(self, question: str) -> dict:
        """
        Retrieve the most relevant document chunks from ChromaDB.
        """

        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        query_embedding = self.embedder.embed_text(question)

        return self.vector_store.search(
            query_embedding=query_embedding,
            n_results=self.top_k,
        )

    def build_context(self, results: dict) -> str:
        """
        Build grounded context from the raw ChromaDB query result.
        """

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        context_parts = []

        for document, metadata in zip(documents, metadatas):
            metadata = metadata or {}

            source = metadata.get("source", "unknown")
            source_name = Path(str(source)).name

            page = metadata.get("page")

            if page is not None:
                try:
                    page_number = int(page) + 1
                    source_label = (
                        f"{source_name}, page {page_number}"
                    )
                except (TypeError, ValueError):
                    source_label = source_name
            else:
                source_label = source_name

            context_parts.append(
                f"[Source: {source_label}]\n"
                f"{document}"
            )

        return "\n\n".join(context_parts)

    def extract_citations(self, results: dict) -> list[dict]:
        """
        Extract unique citations directly from ChromaDB metadata.
        """

        metadatas = results.get("metadatas", [[]])[0]

        citations = []
        seen = set()

        for metadata in metadatas:
            metadata = metadata or {}

            source = metadata.get("source")

            if not source:
                continue

            source_name = Path(str(source)).name

            page = metadata.get("page")

            if page is not None:
                try:
                    page = int(page) + 1
                except (TypeError, ValueError):
                    page = None

            citation_key = (source_name, page)

            if citation_key in seen:
                continue

            seen.add(citation_key)

            citations.append(
                {
                    "source": source_name,
                    "page": page,
                }
            )

        return citations

    def format_citations(self, citations: list[dict]) -> list[str]:
        """
        Convert citation dictionaries into human-readable strings.
        """

        formatted = []

        for citation in citations:
            source = citation["source"]
            page = citation.get("page")

            if page is not None:
                formatted.append(
                    f"{source} — Page {page}"
                )
            else:
                formatted.append(source)

        return formatted

    def generate_answer(
        self,
        question: str,
        context: str,
    ) -> str:
        """
        Generate a grounded answer using the configured LLM provider.
        """

        system_prompt = (
            "You are Nexora, an enterprise knowledge assistant. "
            "Answer the user's question using ONLY the provided "
            "company document context. "
            "Do not use outside knowledge. "
            "Do not invent facts. "
            "If the provided context does not contain enough "
            "information to answer the question, clearly say that "
            "the information is not available in the provided "
            "company documents. "
            "Keep the answer concise and directly answer the question. "
            "Do not create, modify, or invent source names or page numbers."
        )

        user_prompt = f"""
Company document context:

{context}

Question:
{question}

Answer using only the company document context above.
"""

        return self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
            max_tokens=100,
        )

    def ask(self, question: str) -> dict:
        """
        Execute the complete RAG pipeline.
        """

        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        question = question.strip()

        results = self.retrieve(question)

        context = self.build_context(results)

        citations = self.extract_citations(results)

        answer = self.generate_answer(
            question=question,
            context=context,
        )

        return {
            "question": question,
            "answer": answer,
            "context": context,
            "results": results,
            "citations": citations,
            "formatted_citations": self.format_citations(citations),
        }