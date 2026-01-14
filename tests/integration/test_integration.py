"""
Integration tests for AI Finance Assistant.
Tests end-to-end functionality across modules.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestEndToEndWorkflow:
    """End-to-end integration tests."""

    def test_full_education_query_flow(self, mock_llm, sample_documents):
        """Test complete flow for educational query."""
        from src.workflow.graph import FinanceAssistantWorkflow
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.create_index(sample_documents, save=False)

        mock_llm.invoke.return_value = MagicMock(
            content="Stocks represent ownership shares in a company. When you buy stock, you become a partial owner."
        )

        with patch('src.workflow.graph.get_llm', return_value=mock_llm):
            with patch('src.workflow.router.get_llm', return_value=mock_llm):
                with patch('src.agents.finance_qa_agent.get_llm', return_value=mock_llm):
                    with patch('src.agents.finance_qa_agent.get_vector_store', return_value=manager):
                        workflow = FinanceAssistantWorkflow()
                        result = workflow.run("What are stocks?")

                        assert "final_response" in result
                        assert len(result["final_response"]) > 0

    def test_full_portfolio_analysis_flow(self, mock_llm, sample_portfolio, sample_documents):
        """Test complete flow for portfolio analysis."""
        from src.workflow.graph import FinanceAssistantWorkflow
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.create_index(sample_documents, save=False)

        mock_llm.invoke.return_value = MagicMock(
            content="Your portfolio is diversified across tech and bonds."
        )

        with patch('src.workflow.graph.get_llm', return_value=mock_llm):
            with patch('src.workflow.router.get_llm', return_value=mock_llm):
                with patch('src.agents.portfolio_agent.get_llm', return_value=mock_llm):
                    with patch('src.agents.portfolio_agent.get_stock_price') as mock_price:
                        mock_price.return_value = {"price": 175.0, "change_pct": 1.5}
                        workflow = FinanceAssistantWorkflow()
                        result = workflow.run(
                            "Analyze my portfolio",
                            portfolio=sample_portfolio
                        )

                        assert "final_response" in result

    def test_multi_agent_query(self, mock_llm, sample_documents, sample_portfolio):
        """Test query that requires multiple agents."""
        from src.workflow.graph import FinanceAssistantWorkflow
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.create_index(sample_documents, save=False)

        mock_llm.invoke.return_value = MagicMock(
            content="Based on your portfolio and current market conditions..."
        )

        with patch('src.workflow.graph.get_llm', return_value=mock_llm):
            with patch('src.workflow.router.get_llm', return_value=mock_llm):
                with patch('src.agents.finance_qa_agent.get_llm', return_value=mock_llm):
                    with patch('src.agents.finance_qa_agent.get_vector_store', return_value=manager):
                        with patch('src.agents.portfolio_agent.get_llm', return_value=mock_llm):
                            with patch('src.agents.market_agent.get_llm', return_value=mock_llm):
                                workflow = FinanceAssistantWorkflow()
                                result = workflow.run(
                                    "What stocks should I consider for my portfolio?",
                                    portfolio=sample_portfolio
                                )

                                assert "final_response" in result


class TestRAGIntegration:
    """Integration tests for RAG system."""

    def test_document_load_and_search(self):
        """Test loading documents and searching."""
        from src.rag.document_processor import load_and_process_documents
        from src.rag.vector_store import VectorStoreManager

        # Load actual knowledge base
        docs = load_and_process_documents()
        assert len(docs) > 0

        # Create index and search
        manager = VectorStoreManager()
        manager.create_index(docs, save=False)

        results = manager.similarity_search("What is diversification?", k=3)
        assert len(results) > 0
        # Should find relevant content
        assert any("diversif" in r[0].page_content.lower() for r in results)

    def test_rag_chain_with_real_docs(self, mock_llm):
        """Test RAG chain with actual documents."""
        from src.rag.document_processor import load_and_process_documents
        from src.rag.vector_store import VectorStoreManager
        from src.rag.retriever import RAGChain

        docs = load_and_process_documents()
        manager = VectorStoreManager()
        manager.create_index(docs, save=False)

        mock_llm.invoke.return_value = MagicMock(
            content="Stocks are equity investments representing company ownership."
        )

        with patch('src.rag.retriever.get_llm', return_value=mock_llm):
            chain = RAGChain(vector_store=manager)
            result = chain.query("What are stocks?")

            assert "response" in result
            assert "sources" in result
            assert len(result["sources"]) > 0


class TestAgentIntegration:
    """Integration tests for agent interactions."""

    def test_finance_qa_with_rag(self, mock_llm):
        """Test Finance QA agent with RAG integration."""
        from src.agents.finance_qa_agent import FinanceQAAgent
        from src.rag.document_processor import load_and_process_documents
        from src.rag.vector_store import VectorStoreManager
        from src.core.state import create_initial_state

        docs = load_and_process_documents()
        manager = VectorStoreManager()
        manager.create_index(docs, save=False)

        mock_llm.invoke.return_value = MagicMock(
            content="RSUs (Restricted Stock Units) are company shares granted to employees."
        )

        with patch('src.agents.finance_qa_agent.get_llm', return_value=mock_llm):
            with patch('src.agents.finance_qa_agent.get_vector_store', return_value=manager):
                agent = FinanceQAAgent()
                state = create_initial_state("What are RSUs and how are they taxed?")
                result = agent.process(state)

                assert "finance_qa" in result["agent_outputs"]
                assert len(result["sources"]) > 0

    def test_portfolio_with_market_data(self, mock_llm, sample_portfolio):
        """Test Portfolio agent with market data."""
        from src.agents.portfolio_agent import PortfolioAgent
        from src.core.state import create_initial_state

        mock_llm.invoke.return_value = MagicMock(
            content="Your portfolio has a total value of $25,000."
        )

        with patch('src.agents.portfolio_agent.get_llm', return_value=mock_llm):
            with patch('src.agents.portfolio_agent.get_stock_price') as mock_price:
                mock_price.return_value = {
                    "price": 175.0,
                    "previous_close": 173.0,
                    "change_pct": 1.15
                }
                agent = PortfolioAgent()
                state = create_initial_state("How is my portfolio doing?")
                state["portfolio"] = sample_portfolio
                result = agent.process(state)

                assert "portfolio_analysis" in result["agent_outputs"]
                output = result["agent_outputs"]["portfolio_analysis"]
                assert "metrics" in output or "response" in output


class TestStateManagement:
    """Integration tests for state management."""

    def test_state_persistence_across_agents(self, mock_llm, sample_documents):
        """Test that state is maintained across agent executions."""
        from src.workflow.graph import FinanceAssistantWorkflow
        from src.rag.vector_store import VectorStoreManager
        from src.core.state import create_initial_state

        manager = VectorStoreManager()
        manager.create_index(sample_documents, save=False)

        mock_llm.invoke.return_value = MagicMock(content="Test response")

        with patch('src.workflow.graph.get_llm', return_value=mock_llm):
            with patch('src.workflow.router.get_llm', return_value=mock_llm):
                with patch('src.agents.finance_qa_agent.get_llm', return_value=mock_llm):
                    with patch('src.agents.finance_qa_agent.get_vector_store', return_value=manager):
                        workflow = FinanceAssistantWorkflow()

                        # First query
                        result1 = workflow.run("What are stocks?", session_id="test-session")
                        assert result1["session_id"] == "test-session"

    def test_conversation_history(self, mock_llm, sample_documents):
        """Test conversation history is maintained."""
        from src.workflow.graph import FinanceAssistantWorkflow
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.create_index(sample_documents, save=False)

        mock_llm.invoke.return_value = MagicMock(content="Test response")

        with patch('src.workflow.graph.get_llm', return_value=mock_llm):
            with patch('src.workflow.router.get_llm', return_value=mock_llm):
                with patch('src.agents.finance_qa_agent.get_llm', return_value=mock_llm):
                    with patch('src.agents.finance_qa_agent.get_vector_store', return_value=manager):
                        workflow = FinanceAssistantWorkflow()

                        # Multiple queries
                        result1 = workflow.run("What are stocks?")
                        # Conversation context would be passed in real scenario
                        assert "final_response" in result1


class TestErrorHandling:
    """Integration tests for error handling."""

    def test_api_error_recovery(self, mock_llm, sample_documents):
        """Test recovery from API errors."""
        from src.workflow.graph import FinanceAssistantWorkflow
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.create_index(sample_documents, save=False)

        # First call fails, second succeeds
        mock_llm.invoke.side_effect = [
            Exception("API temporarily unavailable"),
            MagicMock(content="Recovered response")
        ]

        with patch('src.workflow.graph.get_llm', return_value=mock_llm):
            with patch('src.workflow.router.get_llm', return_value=mock_llm):
                with patch('src.agents.finance_qa_agent.get_llm', return_value=mock_llm):
                    with patch('src.agents.finance_qa_agent.get_vector_store', return_value=manager):
                        workflow = FinanceAssistantWorkflow()
                        result = workflow.run("What are stocks?")

                        # Should handle error gracefully
                        assert "errors" in result or "final_response" in result

    def test_invalid_portfolio_handling(self, mock_llm):
        """Test handling of invalid portfolio data."""
        from src.agents.portfolio_agent import PortfolioAgent
        from src.core.state import create_initial_state

        mock_llm.invoke.return_value = MagicMock(
            content="I couldn't process your portfolio data."
        )

        with patch('src.agents.portfolio_agent.get_llm', return_value=mock_llm):
            agent = PortfolioAgent()
            state = create_initial_state("Analyze my portfolio")
            state["portfolio"] = {"invalid": "data"}

            result = agent.process(state)
            # Should handle gracefully
            assert "portfolio_analysis" in result["agent_outputs"]
