"""
Retriever module for the RAG system.
Provides the main interface for retrieving relevant documents.
"""

from typing import Dict, List, Optional, Any

from langchain_core.documents import Document

from src.core.config import get_config
from src.rag.vector_store import get_vector_store_manager, VectorStoreManager


class FinanceRetriever:
    """
    Main retriever class for the AI Finance Assistant.
    Retrieves relevant documents from the knowledge base based on queries.
    """

    def __init__(
        self,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None
    ):
        """
        Initialize the retriever.

        Args:
            top_k: Number of documents to retrieve
            score_threshold: Minimum similarity threshold
        """
        config = get_config()
        self.top_k = top_k or config.rag.top_k
        self.score_threshold = score_threshold or config.rag.similarity_threshold
        self._manager: Optional[VectorStoreManager] = None

    @property
    def manager(self) -> VectorStoreManager:
        """Get the vector store manager."""
        if self._manager is None:
            self._manager = get_vector_store_manager()
        return self._manager

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: The search query
            top_k: Number of results to return
            filter_category: Optional category filter

        Returns:
            List of dictionaries with document content, metadata, and scores
        """
        k = top_k or self.top_k

        # Get results with scores
        results = self.manager.similarity_search(
            query=query,
            k=k,
            score_threshold=self.score_threshold
        )

        # Format results
        formatted_results = []
        for doc, score in results:
            # Apply category filter if specified
            if filter_category:
                if doc.metadata.get("category") != filter_category:
                    continue

            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score,
                "source": doc.metadata.get("source", "unknown"),
                "title": doc.metadata.get("title", "Unknown"),
                "url": doc.metadata.get("url")  # Include URL for external sources
            })

        return formatted_results

    def retrieve_with_context(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> str:
        """
        Retrieve relevant documents and format as context string.

        Args:
            query: The search query
            top_k: Number of results to return

        Returns:
            Formatted context string for LLM
        """
        results = self.retrieve(query, top_k)

        if not results:
            return "No relevant information found in the knowledge base."

        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[Source {i}: {result['title']}]\n{result['content']}"
            )

        return "\n\n---\n\n".join(context_parts)

    def get_sources(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[str]:
        """
        Get source references for a query.

        Args:
            query: The search query
            top_k: Number of results

        Returns:
            List of source references
        """
        results = self.retrieve(query, top_k)
        return [result["source"] for result in results]


class RAGChain:
    """
    Combines retrieval with LLM generation for RAG responses.
    """

    def __init__(
        self,
        retriever: Optional[FinanceRetriever] = None,
        top_k: int = 5
    ):
        """
        Initialize the RAG chain.

        Args:
            retriever: Retriever instance (creates default if None)
            top_k: Number of documents to retrieve
        """
        self.retriever = retriever or FinanceRetriever(top_k=top_k)
        self.top_k = top_k

    def get_context(self, query: str) -> Dict[str, Any]:
        """
        Get context and sources for a query.

        Args:
            query: User query

        Returns:
            Dict with context string and source list
        """
        results = self.retriever.retrieve(query, self.top_k)

        # Build context
        context_parts = []
        sources = []

        for result in results:
            context_parts.append(result["content"])
            sources.append({
                "title": result["title"],
                "source": result["source"],
                "score": result["score"],
                "url": result.get("url")  # Include URL for citations
            })

        context = "\n\n---\n\n".join(context_parts) if context_parts else ""

        return {
            "context": context,
            "sources": sources,
            "num_results": len(results)
        }

    def format_prompt_with_context(
        self,
        query: str,
        context: str,
        sources: List[Dict]
    ) -> str:
        """
        Format a prompt with retrieved context.

        Args:
            query: User query
            context: Retrieved context
            sources: Source information

        Returns:
            Formatted prompt string
        """
        source_list = ", ".join([s["title"] for s in sources])

        prompt = f"""Based on the following information from our knowledge base, please answer the user's question.

CONTEXT:
{context}

SOURCES USED: {source_list}

USER QUESTION: {query}

Please provide a clear, educational response. If the context doesn't fully answer the question, say so and provide what information you can. Always maintain a beginner-friendly tone."""

        return prompt


# Convenience functions
def get_retriever(top_k: int = 5) -> FinanceRetriever:
    """Get a configured retriever instance."""
    return FinanceRetriever(top_k=top_k)


def retrieve_context(query: str, top_k: int = 5) -> str:
    """
    Quick retrieval of context for a query.

    Args:
        query: Search query
        top_k: Number of results

    Returns:
        Formatted context string
    """
    retriever = FinanceRetriever(top_k=top_k)
    return retriever.retrieve_with_context(query)
