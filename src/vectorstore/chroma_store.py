from pathlib import Path
from uuid import uuid4

import chromadb
from langchain_core.documents import Document


DEFAULT_COLLECTION_NAME = "nexora_documents"


class ChromaVectorStore:
    """
    Persistent ChromaDB vector store for Nexora document chunks.
    """

    def __init__(
        self,
        persist_directory: str | Path,
        collection_name: str = DEFAULT_COLLECTION_NAME,
    ):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory)
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "description": "Nexora Enterprise knowledge base"
            },
        )

    def add_documents(
        self,
        documents: list[Document],
        embeddings: list[list[float]],
        document_id: str | None = None,
    ) -> list[str]:
        """
        Store document chunks and their embeddings in ChromaDB.
        """

        if len(documents) != len(embeddings):
            raise ValueError(
                "The number of documents must match the number of embeddings."
            )

        if not documents:
            return []

        prefix = document_id or str(uuid4())

        ids = []
        texts = []
        metadatas = []

        for index, document in enumerate(documents):
            chunk_id = f"doc-{prefix}-chunk-{index}"

            ids.append(chunk_id)
            texts.append(document.page_content)

            metadata = {
                key: str(value)
                for key, value in document.metadata.items()
            }

            metadata["document_id"] = prefix
            metadata["chunk_index"] = str(index)

            metadatas.append(metadata)

        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return ids

    def search(
        self,
        query_embedding: list[float],
        n_results: int = 5,
    ) -> dict:
        """
        Search ChromaDB using an embedding vector.

        The caller chooses the candidate pool size for reranking.
        """

        if not query_embedding:
            raise ValueError("Query embedding cannot be empty.")

        if n_results <= 0:
            raise ValueError("n_results must be greater than 0.")

        # Chroma cannot return more results than exist in the collection.
        total_documents = self.collection.count()
        candidate_count = min(n_results, total_documents)

        if candidate_count == 0:
            return {
                "ids": [[]],
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
            }

        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=candidate_count,
        )

    def get_all_documents(self) -> dict:
        """
        Return all stored document chunks and their metadata.

        This is used by the hybrid retrieval layer to perform
        keyword-based matching in addition to semantic retrieval.
        """

        return self.collection.get(
            include=[
                "documents",
                "metadatas",
            ]
        )

    def delete(self, ids: list[str]) -> None:
        """Delete vectors from the collection by ID."""

        if not ids:
            return

        self.collection.delete(ids=ids)

    def delete_by_document_id(self, document_id: str) -> None:
        """Delete all chunks belonging to a document."""

        if not document_id:
            raise ValueError("Document ID cannot be empty.")

        self.collection.delete(
            where={"document_id": document_id}
        )

    def count(self) -> int:
        """Return the number of stored chunks."""

        return self.collection.count()

    def get_statistics(self) -> dict:
        """Return live chunk totals grouped by their stored source metadata."""

        snapshot = self.get_all_documents()
        grouped = {}

        for metadata in snapshot.get("metadatas") or []:
            metadata = metadata or {}
            document_id = metadata.get("document_id")
            source = metadata.get("source", "unknown")
            key = (document_id, source)

            if key not in grouped:
                grouped[key] = {
                    "document_id": document_id,
                    "source": source,
                    "chunks": 0,
                }

            grouped[key]["chunks"] += 1

        documents = sorted(
            grouped.values(),
            key=lambda document: (document["source"].lower(), document["document_id"] or ""),
        )

        return {
            "total_chunks": len(snapshot.get("ids") or []),
            "indexed_documents": len(documents),
            "documents": documents,
        }
