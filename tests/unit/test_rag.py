"""
Unit tests for the RAG module (embeddings, document_processor, vector_store, retriever).
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain_core.documents import Document


class TestEmbeddings:
    """Tests for embeddings module."""

    def test_embeddings_manager_singleton(self):
        """Test that EmbeddingsManager is a singleton."""
        from src.rag.embeddings import EmbeddingsManager, _embeddings_instance

        # Reset singleton for test
        import src.rag.embeddings as emb_module
        emb_module._embeddings_instance = None

        manager1 = EmbeddingsManager()
        manager2 = EmbeddingsManager()

        # Should be same instance
        assert manager1 is manager2

    def test_get_embeddings_function(self):
        """Test get_embeddings convenience function."""
        from src.rag.embeddings import get_embeddings

        embeddings = get_embeddings()
        assert embeddings is not None

    def test_embeddings_model_name(self):
        """Test that correct model is used."""
        from src.rag.embeddings import EmbeddingsManager
        import src.rag.embeddings as emb_module
        emb_module._embeddings_instance = None

        manager = EmbeddingsManager()
        assert manager.model_name == "all-MiniLM-L6-v2"


class TestDocumentProcessor:
    """Tests for document processor module."""

    def test_create_text_splitter(self):
        """Test text splitter creation."""
        from src.rag.document_processor import create_text_splitter

        splitter = create_text_splitter(chunk_size=500, chunk_overlap=100)
        assert splitter._chunk_size == 500
        assert splitter._chunk_overlap == 100

    def test_process_document(self):
        """Test document processing into chunks."""
        from src.rag.document_processor import process_document

        doc = Document(
            page_content="This is a test document. " * 100,  # Long content
            metadata={"source": "test.md", "title": "Test"}
        )

        chunks = process_document(doc, chunk_size=200, chunk_overlap=50)

        assert len(chunks) > 1  # Should be split
        for chunk in chunks:
            assert chunk.metadata["source"] == "test.md"

    def test_extract_metadata_from_markdown(self):
        """Test metadata extraction from markdown content."""
        from src.rag.document_processor import extract_metadata_from_markdown

        content = """# Test Title

This is the content of the document.

## Section 1
More content here.
"""
        metadata = extract_metadata_from_markdown(content, "test_file.md")

        assert metadata["title"] == "Test Title"
        assert metadata["source"] == "test_file.md"

    def test_extract_metadata_no_title(self):
        """Test metadata extraction when no title is present."""
        from src.rag.document_processor import extract_metadata_from_markdown

        content = "Just some content without a title header."
        metadata = extract_metadata_from_markdown(content, "no_title.md")

        assert "source" in metadata

    def test_load_and_process_documents(self):
        """Test loading documents from knowledge base."""
        from src.rag.document_processor import load_and_process_documents

        # This will load from actual knowledge base
        docs = load_and_process_documents()

        assert len(docs) > 0
        assert all(isinstance(d, Document) for d in docs)


class TestVectorStore:
    """Tests for vector store module."""

    def test_vector_store_manager_init(self):
        """Test VectorStoreManager initialization."""
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        assert manager.embeddings is not None

    def test_create_index(self, sample_documents):
        """Test creating FAISS index."""
        from src.rag.vector_store import VectorStoreManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = VectorStoreManager()
            manager.index_path = Path(tmpdir) / "test_index"

            manager.create_index(sample_documents, save=True)

            assert manager.index is not None
            assert (Path(tmpdir) / "test_index").exists()

    def test_load_index(self, sample_documents):
        """Test loading existing FAISS index."""
        from src.rag.vector_store import VectorStoreManager

        with tempfile.TemporaryDirectory() as tmpdir:
            # First create an index
            manager1 = VectorStoreManager()
            manager1.index_path = Path(tmpdir) / "test_index"
            manager1.create_index(sample_documents, save=True)

            # Then load it
            manager2 = VectorStoreManager()
            manager2.index_path = Path(tmpdir) / "test_index"
            loaded = manager2.load_index()

            assert loaded is True
            assert manager2.index is not None

    def test_similarity_search(self, sample_documents):
        """Test similarity search on index."""
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.create_index(sample_documents, save=False)

        results = manager.similarity_search("What are stocks?", k=2)

        assert len(results) <= 2
        assert all(isinstance(r[0], Document) for r in results)
        assert all(isinstance(r[1], float) for r in results)

    def test_similarity_search_no_index(self):
        """Test similarity search with no index raises error."""
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.index = None

        with pytest.raises(ValueError, match="No index loaded"):
            manager.similarity_search("test query")

    def test_add_documents(self, sample_documents):
        """Test adding documents to existing index."""
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.create_index(sample_documents[:2], save=False)

        # Add more documents
        new_doc = Document(
            page_content="New document about mutual funds.",
            metadata={"source": "new_doc.md"}
        )
        manager.add_documents([new_doc])

        # Should be searchable
        results = manager.similarity_search("mutual funds", k=1)
        assert len(results) > 0


class TestRetriever:
    """Tests for retriever module."""

    def test_finance_retriever_init(self, sample_documents):
        """Test FinanceRetriever initialization."""
        from src.rag.retriever import FinanceRetriever
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.create_index(sample_documents, save=False)

        retriever = FinanceRetriever(vector_store=manager)
        assert retriever.top_k == 5
        assert retriever.score_threshold == 0.7

    def test_finance_retriever_retrieve(self, sample_documents):
        """Test retrieving relevant documents."""
        from src.rag.retriever import FinanceRetriever
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.create_index(sample_documents, save=False)

        retriever = FinanceRetriever(vector_store=manager, score_threshold=0.0)
        results = retriever.retrieve("What are stocks?")

        assert len(results) > 0
        assert all(isinstance(r, Document) for r in results)

    def test_finance_retriever_format_context(self, sample_documents):
        """Test formatting retrieved documents as context."""
        from src.rag.retriever import FinanceRetriever
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.create_index(sample_documents, save=False)

        retriever = FinanceRetriever(vector_store=manager, score_threshold=0.0)
        context = retriever.get_formatted_context("What are stocks?")

        assert isinstance(context, str)
        assert len(context) > 0

    def test_rag_chain_init(self, sample_documents, mock_llm):
        """Test RAGChain initialization."""
        from src.rag.retriever import RAGChain
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.create_index(sample_documents, save=False)

        with patch('src.rag.retriever.get_llm', return_value=mock_llm):
            chain = RAGChain(vector_store=manager)
            assert chain.retriever is not None

    def test_rag_chain_query(self, sample_documents, mock_llm):
        """Test RAGChain query execution."""
        from src.rag.retriever import RAGChain
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.create_index(sample_documents, save=False)

        mock_llm.invoke.return_value = MagicMock(content="Stocks are ownership shares in companies.")

        with patch('src.rag.retriever.get_llm', return_value=mock_llm):
            chain = RAGChain(vector_store=manager)
            result = chain.query("What are stocks?")

            assert "response" in result
            assert "sources" in result


class TestGetVectorStore:
    """Tests for get_vector_store convenience function."""

    def test_get_vector_store_creates_new(self, sample_documents):
        """Test get_vector_store creates new index if needed."""
        from src.rag.vector_store import get_vector_store
        import src.rag.vector_store as vs_module

        # Reset singleton
        vs_module._vector_store_instance = None

        with patch.object(vs_module.VectorStoreManager, 'load_index', return_value=False):
            with patch.object(vs_module.VectorStoreManager, 'create_index'):
                with patch('src.rag.vector_store.load_and_process_documents', return_value=sample_documents):
                    store = get_vector_store()
                    assert store is not None
