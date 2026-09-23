from pathlib import Path

from ingestion.loader import load_document
from chunking.splitter import split_documents
from embeddings.embedder import DocumentEmbedder
from vectorstore.chroma_store import ChromaVectorStore


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma"


def index_document(
    file_path: str | Path,
    document_id: str | None = None,
    display_name: str | None = None,
) -> dict:
    """
    Load, chunk, embed, and store a single document in ChromaDB.

    display_name is the user-facing filename that should appear in
    citations. If it is not provided, the actual file name is used.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")

    print(f"Indexing document: {path.name}")

    documents = load_document(path)

    if not documents:
        raise ValueError("Document contains no readable content.")

    user_facing_name = display_name or path.name

    for document in documents:
        document.metadata["source"] = user_facing_name

    chunks = split_documents(
        documents,
        chunk_size=500,
        chunk_overlap=50,
    )

    if not chunks:
        raise ValueError("Document produced no chunks.")

    for chunk in chunks:
        chunk.metadata["source"] = user_facing_name

    embedder = DocumentEmbedder()
    embeddings = embedder.embed_documents(chunks)

    vector_store = ChromaVectorStore(
        persist_directory=CHROMA_DIR,
    )

    vector_store.add_documents(
        documents=chunks,
        embeddings=embeddings,
        document_id=document_id,
    )

    return {
        "filename": user_facing_name,
        "documents": len(documents),
        "chunks": len(chunks),
        "vectors": vector_store.count(),
    }