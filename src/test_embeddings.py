from pathlib import Path

import numpy as np

from ingestion.loader import load_documents_from_folder
from chunking.splitter import split_documents
from embeddings.embedder import DocumentEmbedder


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "sample_documents"


def cosine_similarity(vector_a, vector_b):
    """
    Calculate cosine similarity between two vectors.
    """

    a = np.array(vector_a)
    b = np.array(vector_b)

    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def main():
    print("=" * 70)
    print("MODULE 4 - EMBEDDINGS TEST")
    print("=" * 70)

    print("\nLoading documents...")

    documents = load_documents_from_folder(DOCUMENTS_DIR)

    print(f"\nOriginal documents: {len(documents)}")

    chunks = split_documents(
        documents,
        chunk_size=500,
        chunk_overlap=50,
    )

    print(f"Chunks generated: {len(chunks)}")

    print("\nLoading embedding model...")

    embedder = DocumentEmbedder()

    dimension = embedder.get_embedding_dimension()

    print(f"Embedding model: {embedder.model_name}")
    print(f"Embedding dimension: {dimension}")

    print("\nGenerating document embeddings...")

    embeddings = embedder.embed_documents(chunks)

    print(f"Number of embeddings: {len(embeddings)}")

    for index, embedding in enumerate(embeddings, start=1):
        print(f"\nEmbedding #{index}")
        print("-" * 70)
        print(f"Vector dimensions: {len(embedding)}")
        print(f"First 10 values: {embedding[:10]}")

        magnitude = np.linalg.norm(np.array(embedding))

        print(f"Vector magnitude: {magnitude:.6f}")

    # ------------------------------------------------------------------
    # Semantic similarity test
    # ------------------------------------------------------------------

    print("\n" + "=" * 70)
    print("SEMANTIC SIMILARITY TEST")
    print("=" * 70)

    query = "How many paid leave days do employees receive?"

    print(f"\nQuery:")
    print(query)

    query_embedding = embedder.embed_text(query)

    similarities = []

    for index, embedding in enumerate(embeddings):
        similarity = cosine_similarity(query_embedding, embedding)

        similarities.append(similarity)

        source = Path(
            chunks[index].metadata.get("source", "unknown")
        ).name

        print(
            f"\nChunk #{index + 1} - {source}"
        )
        print(f"Cosine similarity: {similarity:.4f}")

    best_index = int(np.argmax(similarities))

    best_source = Path(
        chunks[best_index].metadata.get("source", "unknown")
    ).name

    print("\n" + "-" * 70)
    print(f"Most similar document: {best_source}")
    print(f"Similarity score: {similarities[best_index]:.4f}")

    # ------------------------------------------------------------------
    # Assertions
    # ------------------------------------------------------------------

    assert len(embeddings) == len(chunks)

    assert dimension == 384

    for embedding in embeddings:
        assert len(embedding) == 384

        magnitude = np.linalg.norm(np.array(embedding))
        assert abs(magnitude - 1.0) < 0.001

    # The leave FAQ should be the most relevant document for this query.
    assert best_source == "company_faq.txt"

    print("\n" + "=" * 70)
    print("ALL EMBEDDING TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()