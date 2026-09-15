from pathlib import Path

from ingestion.loader import load_document
from chunking.splitter import split_documents
from embeddings.embedder import DocumentEmbedder
from vectorstore.chroma_store import ChromaVectorStore


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma"


def index_document(file_path: str | Path) -> dict:
    """
    Load, chunk, embed, and store a single document in ChromaDB.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")

    print(f"Indexing document: {path.name}")

    documents = load_document(path)

    if not documents:
        raise ValueError("Document contains no readable content.")

    chunks = split_documents(
        documents,
        chunk_size=500,
        chunk_overlap=50,
    )

    if not chunks:
        raise ValueError("Document produced no chunks.")

    embedder = DocumentEmbedder()

    embeddings = embedder.embed_documents(chunks)

    vector_store = ChromaVectorStore(
        persist_directory=CHROMA_DIR,
    )

    vector_store.add_documents(
        documents=chunks,
        embeddings=embeddings,
    )

    return {
        "filename": path.name,
        "documents": len(documents),
        "chunks": len(chunks),
        "vectors": vector_store.count(),
    }