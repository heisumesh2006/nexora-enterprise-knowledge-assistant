import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from embeddings.embedder import DocumentEmbedder
from vectorstore.chroma_store import ChromaVectorStore


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma"


class RAGChain:
    """
    Basic Retrieval-Augmented Generation pipeline.

    Flow:
        Question
            ↓
        Query Embedding
            ↓
        ChromaDB Retrieval
            ↓
        Context Construction
            ↓
        NVIDIA NeMoTron
            ↓
        Answer
    """

    def __init__(
        self,
        chroma_directory: str | Path = CHROMA_DIR,
        top_k: int = 3,
    ):
        load_dotenv()

        self.model = os.getenv(
            "NVIDIA_MODEL",
            "nvidia/nemotron-3-ultra-550b-a55b",
        )

        self.base_url = os.getenv(
            "NVIDIA_BASE_URL",
            "https://integrate.api.nvidia.com/v1",
        )

        api_key = os.getenv("NVIDIA_API_KEY")

        if not api_key:
            raise ValueError(
                "NVIDIA_API_KEY is not configured in the environment."
            )

        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")

        self.top_k = top_k

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=api_key,
        )

        self.embedder = DocumentEmbedder()

        self.vector_store = ChromaVectorStore(
            persist_directory=chroma_directory,
        )

    def retrieve(self, question: str) -> dict:
        """
        Retrieve the most relevant document chunks for a question.
        """

        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        query_embedding = self.embedder.embed_text(question)

        return self.vector_store.search(
            query_embedding=query_embedding,
            n_results=self.top_k,
        )

    def build_context(self, results: dict) -> str:
        """
        Convert retrieved ChromaDB results into an LLM context string.
        """

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        context_parts = []

        for index, document in enumerate(documents):
            metadata = (
                metadatas[index]
                if index < len(metadatas)
                else {}
            )

            source = Path(
                metadata.get("source", "unknown")
            ).name

            page = metadata.get("page")

            if page is not None:
                source_label = f"{source}, page {int(page) + 1}"
            else:
                source_label = source

            context_parts.append(
                f"[Source: {source_label}]\n{document}"
            )

        return "\n\n".join(context_parts)

    def generate_answer(
        self,
        question: str,
        context: str,
    ) -> str:
        """
        Generate an answer using only the retrieved context.
        """

        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        if not context.strip():
            raise ValueError("Context cannot be empty.")

        system_prompt = """
You are Nexora Enterprise's knowledge assistant.

Answer the user's question using ONLY the information provided
in the context.

Rules:
1. Do not invent or assume information.
2. If the context does not contain enough information to answer
   the question, clearly say that the information is not available
   in the provided company documents.
3. Keep the answer concise and directly answer the question.
4. Do not use outside knowledge.
"""

        user_prompt = f"""
Context:
{context}

Question:
{question}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt.strip(),
                },
                {
                    "role": "user",
                    "content": user_prompt.strip(),
                },
            ],
            temperature=0.2,
            max_tokens=300,
        )

        return response.choices[0].message.content.strip()

    def ask(self, question: str) -> dict:
        """
        Run the complete RAG pipeline.
        """

        results = self.retrieve(question)

        context = self.build_context(results)

        answer = self.generate_answer(
            question=question,
            context=context,
        )

        return {
            "question": question,
            "answer": answer,
            "context": context,
            "results": results,
        }