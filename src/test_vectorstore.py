from pathlib import Path

from ingestion.loader import load_documents_from_folder
from chunking.splitter import split_documents
from embeddings.embedder import DocumentEmbedder
from vectorstore.chroma_store import ChromaVectorStore


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "sample_documents"
TEST_DB_DIR = PROJECT_ROOT / "data" / "chroma_test"


def main():
    print("=" * 70)
    print("MODULE 5 - CHROMADB PERSISTENCE TEST")
    print("=" * 70)

    # ---------------------------------------------------------------
    # Load and prepare documents
    # ---------------------------------------------------------------

    print("\nLoading documents...")

    documents = load_documents_from_folder(DOCUMENTS_DIR)

    print(f"Original documents: {len(documents)}")

    chunks = split_documents(
        documents,
        chunk_size=500,
        chunk_overlap=50,
    )

    print(f"Chunks generated: {len(chunks)}")

    # ---------------------------------------------------------------
    # Load embedding model
    # ---------------------------------------------------------------

    print("\nLoading embedding model...")

    embedder = DocumentEmbedder()

    print(f"Embedding model: {embedder.model_name}")
    print(f"Embedding dimension: {embedder.get_embedding_dimension()}")

    # ---------------------------------------------------------------
    # Create/open persistent ChromaDB
    # ---------------------------------------------------------------

    print("\nOpening persistent ChromaDB...")

    vector_store = ChromaVectorStore(
        persist_directory=TEST_DB_DIR,
    )

    existing_count = vector_store.count()

    print(f"Existing vectors in database: {existing_count}")

    # ---------------------------------------------------------------
    # Index documents only when database is empty
    # ---------------------------------------------------------------

    if existing_count == 0:
        print("\nDatabase is empty.")
        print("Generating document embeddings...")

        embeddings = embedder.embed_documents(chunks)

        print(f"Embeddings generated: {len(embeddings)}")

        print("\nAdding documents to ChromaDB...")

        vector_store.add_documents(
            documents=chunks,
            embeddings=embeddings,
        )

        print(f"Vectors stored: {vector_store.count()}")

    else:
        print("\nDatabase already contains vectors.")
        print("Skipping document embedding/indexing.")

    # ---------------------------------------------------------------
    # Semantic search
    # ---------------------------------------------------------------

    query = "How many paid leave days do employees receive?"

    print("\n" + "=" * 70)
    print("SEMANTIC SEARCH TEST")
    print("=" * 70)

    print(f"\nQuery:")
    print(query)

    print("\nGenerating query embedding...")

    query_embedding = embedder.embed_text(query)

    results = vector_store.search(
        query_embedding=query_embedding,
        n_results=3,
    )

    result_documents = results["documents"][0]
    result_metadatas = results["metadatas"][0]
    result_distances = results["distances"][0]

    print(f"\nRetrieved results: {len(result_documents)}")

    for index, (
        document,
        metadata,
        distance,
    ) in enumerate(
        zip(
            result_documents,
            result_metadatas,
            result_distances,
        ),
        start=1,
    ):
        source = Path(
            metadata.get("source", "unknown")
        ).name

        print("\n" + "-" * 70)
        print(f"Result #{index}")
        print(f"Source: {source}")
        print(f"Distance: {distance:.4f}")
        print(f"Content:\n{document}")

    # ---------------------------------------------------------------
    # Validation
    # ---------------------------------------------------------------

    assert vector_store.count() == 3

    assert len(result_documents) == 3

    top_source = Path(
        result_metadatas[0].get("source", "unknown")
    ).name

    assert top_source == "company_faq.txt"

    assert "18 days" in result_documents[0]

    print("\n" + "=" * 70)
    print("ALL CHROMADB TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()