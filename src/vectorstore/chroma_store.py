from pathlib import Path

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
    ) -> None:
        """
        Store document chunks and their embeddings in ChromaDB.
        """

        if len(documents) != len(embeddings):
            raise ValueError(
                "The number of documents must match the number of embeddings."
            )

        if not documents:
            return

        ids = []
        texts = []
        metadatas = []

        for index, document in enumerate(documents):
            ids.append(f"chunk-{index}")
            texts.append(document.page_content)

            metadata = {
                key: str(value)
                for key, value in document.metadata.items()
            }

            metadatas.append(metadata)

        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

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

    def count(self) -> int:
        """
        Return the number of stored chunks.
        """

        return self.collection.count()