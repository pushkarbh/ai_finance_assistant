"""
Vector store module for the RAG system.
Manages FAISS index creation, storage, and retrieval.
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from src.core.config import get_config
from src.rag.embeddings import get_embeddings
from src.rag.document_processor import load_and_process_documents


class VectorStoreManager:
    """
    Manages the FAISS vector store for the RAG system.
    Handles index creation, persistence, and loading.
    """

    def __init__(self):
        """Initialize the vector store manager."""
        self.config = get_config()
        self.index_path = self.config.faiss_index_path
        self.embeddings = get_embeddings()
        self._vector_store: Optional[FAISS] = None

    @property
    def vector_store(self) -> Optional[FAISS]:
        """Get the current vector store instance."""
        return self._vector_store

    def create_index(
        self,
        documents: Optional[List[Document]] = None,
        save: bool = True
    ) -> FAISS:
        """
        Create a new FAISS index from documents.

        Args:
            documents: Documents to index (if None, loads from knowledge base)
            save: Whether to save the index to disk

        Returns:
            FAISS vector store instance
        """
        if documents is None:
            documents = load_and_process_documents()

        if not documents:
            raise ValueError("No documents provided for indexing")

        print(f"Creating FAISS index with {len(documents)} documents...")

        # Create FAISS index
        self._vector_store = FAISS.from_documents(
            documents=documents,
            embedding=self.embeddings
        )

        if save:
            self.save_index()

        print("FAISS index created successfully")
        return self._vector_store

    def save_index(self, path: Optional[Path] = None):
        """
        Save the FAISS index to disk.

        Args:
            path: Path to save to (default: config.faiss_index_path)
        """
        if self._vector_store is None:
            raise ValueError("No vector store to save. Create an index first.")

        save_path = path or self.index_path

        # Create directory if it doesn't exist
        save_path.mkdir(parents=True, exist_ok=True)

        # Save the index
        self._vector_store.save_local(str(save_path))
        print(f"FAISS index saved to {save_path}")

    def load_index(self, path: Optional[Path] = None) -> FAISS:
        """
        Load a FAISS index from disk.

        Args:
            path: Path to load from (default: config.faiss_index_path)

        Returns:
            FAISS vector store instance
        """
        load_path = path or self.index_path

        if not load_path.exists():
            raise FileNotFoundError(f"FAISS index not found at {load_path}")

        print(f"Loading FAISS index from {load_path}...")
        self._vector_store = FAISS.load_local(
            str(load_path),
            self.embeddings,
            allow_dangerous_deserialization=True
        )

        print("FAISS index loaded successfully")
        return self._vector_store

    def get_or_create_index(self) -> FAISS:
        """
        Get existing index or create a new one.

        Returns:
            FAISS vector store instance
        """
        if self._vector_store is not None:
            return self._vector_store

        # Try to load existing index
        if self.index_path.exists():
            try:
                return self.load_index()
            except Exception as e:
                print(f"Error loading index: {e}. Creating new index...")

        # Create new index
        return self.create_index()

    def similarity_search(
        self,
        query: str,
        k: int = None,
        score_threshold: float = None
    ) -> List[Tuple[Document, float]]:
        """
        Search for similar documents.

        Args:
            query: Search query
            k: Number of results (default from config)
            score_threshold: Minimum similarity score (default from config)

        Returns:
            List of (document, score) tuples
        """
        if self._vector_store is None:
            self.get_or_create_index()

        k = k or self.config.rag.top_k
        score_threshold = score_threshold or self.config.rag.similarity_threshold

        # Get results with scores
        results = self._vector_store.similarity_search_with_score(
            query,
            k=k
        )

        # Filter by score threshold (lower score = more similar in FAISS)
        # Note: FAISS uses L2 distance, so lower is better
        filtered_results = []
        for doc, score in results:
            # Convert L2 distance to similarity (approximate)
            similarity = 1 / (1 + score)
            if similarity >= score_threshold:
                filtered_results.append((doc, similarity))

        return filtered_results

    def add_documents(self, documents: List[Document]):
        """
        Add new documents to the existing index.

        Args:
            documents: Documents to add
        """
        if self._vector_store is None:
            self.get_or_create_index()

        self._vector_store.add_documents(documents)
        self.save_index()


# Singleton instance
_vector_store_manager: Optional[VectorStoreManager] = None


def get_vector_store_manager() -> VectorStoreManager:
    """Get the singleton vector store manager."""
    global _vector_store_manager
    if _vector_store_manager is None:
        _vector_store_manager = VectorStoreManager()
    return _vector_store_manager


def get_vector_store() -> FAISS:
    """
    Get the FAISS vector store, creating it if necessary.

    Returns:
        FAISS vector store instance
    """
    manager = get_vector_store_manager()
    return manager.get_or_create_index()
