"""
Embeddings module for the RAG system.
Uses sentence-transformers for local, free embeddings.
"""

from typing import List

from langchain_community.embeddings import HuggingFaceEmbeddings

from src.core.config import get_config


class EmbeddingsManager:
    """
    Manages embeddings generation using sentence-transformers.
    Uses the all-MiniLM-L6-v2 model by default for fast, quality embeddings.
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern to reuse the model."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the embeddings model."""
        if self._initialized:
            return

        config = get_config()
        self.model_name = config.embeddings.model
        self.dimension = config.embeddings.dimension

        # Initialize HuggingFace embeddings
        self._embeddings = HuggingFaceEmbeddings(
            model_name=f"sentence-transformers/{self.model_name}",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        self._initialized = True

    @property
    def embeddings(self) -> HuggingFaceEmbeddings:
        """Get the underlying LangChain embeddings instance."""
        return self._embeddings

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: The text to embed

        Returns:
            List of floats representing the embedding vector
        """
        return self._embeddings.embed_query(text)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        return self._embeddings.embed_documents(texts)


def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Get the singleton embeddings instance.

    Returns:
        Configured HuggingFaceEmbeddings instance
    """
    return EmbeddingsManager().embeddings
