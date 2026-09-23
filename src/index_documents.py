from pathlib import Path

from ingestion.loader import load_documents_from_folder
from chunking.splitter import split_documents
from embeddings.embedder import DocumentEmbedder
from vectorstore.chroma_store import ChromaVectorStore


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "sample_documents"
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma"


def main():
    print("=" * 70)
    print("NEXORA - DOCUMENT INDEXING")
    print("=" * 70)

    print("\nLoading documents...")

    documents = load_documents_from_folder(DOCUMENTS_DIR)

    print(f"Documents loaded: {len(documents)}")

    print("\nChunking documents...")

    chunks = split_documents(
        documents,
        chunk_size=500,
        chunk_overlap=50,
    )

    print(f"Chunks generated: {len(chunks)}")

    print("\nLoading embedding model...")

    embedder = DocumentEmbedder()

    print(f"Embedding model: {embedder.model_name}")

    print("\nGenerating embeddings...")

    embeddings = embedder.embed_documents(chunks)

    print(f"Embeddings generated: {len(embeddings)}")

    print("\nOpening ChromaDB...")

    vector_store = ChromaVectorStore(
        persist_directory=CHROMA_DIR,
    )

    print("\nAdding documents to vector database...")

    vector_store.add_documents(
    documents=chunks,
    embeddings=embeddings,
    document_id="sample-documents",
)

    print(f"Vectors stored: {vector_store.count()}")

    print("\n" + "=" * 70)
    print("DOCUMENT INDEXING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()