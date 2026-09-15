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

        A document_id can be supplied so every chunk receives a
        globally unique ID.
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
        n_results: int = 3,
    ) -> dict:
        """
        Search ChromaDB using an embedding vector.
        """

        if not query_embedding:
            raise ValueError("Query embedding cannot be empty.")

        if n_results <= 0:
            raise ValueError("n_results must be greater than 0.")

        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
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
        """
        Return the number of stored chunks.
        """

        return self.collection.count()