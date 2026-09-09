from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer


DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class DocumentEmbedder:
    """
    Generates vector embeddings for text and LangChain Documents.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text: str) -> list[float]:
        """
        Generate an embedding vector for a single text string.
        """

        if not text or not text.strip():
            raise ValueError("Text cannot be empty.")

        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return embedding.tolist()

    def embed_documents(self, documents: list[Document]) -> list[list[float]]:
        """
        Generate embeddings for a list of LangChain Documents.
        """

        if not documents:
            return []

        texts = [document.page_content for document in documents]

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        return embeddings.tolist()

    def get_embedding_dimension(self) -> int:
        """
        Return the dimensionality of the embedding vectors.
        """

        return self.model.get_embedding_dimension()