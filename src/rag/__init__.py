"""
RAG (Retrieval-Augmented Generation) module for AI Finance Assistant.
Provides document processing, embeddings, vector storage, and retrieval.
"""

from src.rag.embeddings import (
    EmbeddingsManager,
    get_embeddings
)

from src.rag.document_processor import (
    DocumentProcessor,
    load_and_process_documents
)

from src.rag.vector_store import (
    VectorStoreManager,
    get_vector_store_manager,
    get_vector_store
)

from src.rag.retriever import (
    FinanceRetriever,
    RAGChain,
    get_retriever,
    retrieve_context
)

__all__ = [
    # Embeddings
    "EmbeddingsManager",
    "get_embeddings",
    # Document Processing
    "DocumentProcessor",
    "load_and_process_documents",
    # Vector Store
    "VectorStoreManager",
    "get_vector_store_manager",
    "get_vector_store",
    # Retriever
    "FinanceRetriever",
    "RAGChain",
    "get_retriever",
    "retrieve_context",
]
