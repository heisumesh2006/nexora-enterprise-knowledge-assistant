import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


# Add the project's src directory to Python's import path.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from rag.chain import RAGChain


app = FastAPI(
    title="Nexora AI Service",
    description="RAG-powered enterprise knowledge assistant service",
    version="1.0.0",
)


class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="Question to ask the enterprise knowledge assistant.",
    )


class Citation(BaseModel):
    source: str
    page: int | None = None


class AskResponse(BaseModel):
    question: str
    answer: str
    citations: list[Citation]


print("Initializing Nexora RAG service...")

rag = RAGChain(
    top_k=3,
)

print("Nexora RAG service initialized successfully.")


@app.get("/health")
def health_check():
    """
    Health check endpoint.
    """

    return {
        "status": "ok",
        "service": "nexora-ai-service",
    }


@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    """
    Ask a question against the indexed enterprise documents.
    """

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