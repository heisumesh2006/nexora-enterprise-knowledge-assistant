import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from indexer import index_document
from rag.chain import RAGChain


app = FastAPI(
    title="Nexora AI Service",
    description="RAG-powered enterprise knowledge assistant service",
    version="1.0.0",
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)


class IndexRequest(BaseModel):
    file_path: str = Field(..., min_length=1)
    document_id: str = Field(..., min_length=1)


class Citation(BaseModel):
    source: str
    page: int | None = None


class AskResponse(BaseModel):
    question: str
    answer: str
    citations: list[Citation]


class IndexResponse(BaseModel):
    message: str
    filename: str
    documents: int
    chunks: int
    vectors: int


print("Initializing Nexora RAG service...")

rag = RAGChain(top_k=3)

print("Nexora RAG service initialized successfully.")


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "nexora-ai-service",
    }


@app.get("/stats")
def knowledge_base_stats():
    """Report counts directly from the persistent Chroma collection."""

    try:
        return rag.vector_store.get_statistics()
    except Exception as exc:
        print(f"Knowledge-base statistics failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Failed to read knowledge-base statistics.",
        ) from exc


@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    try:
        result = rag.ask(question)

        return AskResponse(
            question=result["question"],
            answer=result["answer"],
            citations=result["citations"],
        )

    except Exception as exc:
        print(f"RAG request failed: {exc}")

        raise HTTPException(
            status_code=500,
            detail="Failed to process the question.",
        ) from exc


@app.post("/index", response_model=IndexResponse)
def index_uploaded_document(request: IndexRequest):
    file_path = Path(request.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Document file not found.",
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=400,
            detail="Provided path is not a file.",
        )

    try:
        result = index_document(
            file_path=file_path,
            document_id=request.document_id,
        )

        return IndexResponse(
            message="Document indexed successfully.",
            filename=result["filename"],
            documents=result["documents"],
            chunks=result["chunks"],
            vectors=result["vectors"],
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        print(f"Document indexing failed: {exc}")

        raise HTTPException(
            status_code=500,
            detail="Failed to index document.",
        ) from exc
