"""
Unit tests for the workflow module (router, graph).
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestQueryRouter:
    """Tests for QueryRouter class."""

    def test_router_init(self, mock_llm):
        """Test QueryRouter initialization."""
        from src.workflow.router import QueryRouter

        with patch('src.workflow.router.get_llm', return_value=mock_llm):
            router = QueryRouter()
            assert router is not None

    def test_route_education_query(self, mock_llm):
        """Test routing educational queries."""
        from src.workflow.router import QueryRouter

        with patch('src.workflow.router.get_llm', return_value=mock_llm):
            router = QueryRouter()
            result = router.route("What are stocks and how do they work?")

            assert "finance_qa" in result["agents"]

    def test_route_portfolio_query(self, mock_llm):
        """Test routing portfolio queries."""
        from src.workflow.router import QueryRouter

        with patch('src.workflow.router.get_llm', return_value=mock_llm):
            router = QueryRouter()
            result = router.route("Analyze my portfolio holdings")

            assert "portfolio_analysis" in result["agents"]

    def test_route_market_query(self, mock_llm):
        """Test routing market queries."""
        from src.workflow.router import QueryRouter

        with patch('src.workflow.router.get_llm', return_value=mock_llm):
            router = QueryRouter()
            result = router.route("What is the current price of AAPL?")

            assert "market_analysis" in result["agents"]

    def test_route_goal_query(self, mock_llm):
        """Test routing goal planning queries."""
        from src.workflow.router import QueryRouter

        with patch('src.workflow.router.get_llm', return_value=mock_llm):
            router = QueryRouter()
            result = router.route("Help me plan for retirement")

            assert "goal_planning" in result["agents"]

    def test_route_news_query(self, mock_llm):
        """Test routing news queries."""
        from src.workflow.router import QueryRouter

        with patch('src.workflow.router.get_llm', return_value=mock_llm):
            router = QueryRouter()
            result = router.route("What's the latest news about tech stocks?")

            assert "news_synthesizer" in result["agents"]

    def test_route_multi_agent_query(self, mock_llm):
        """Test routing queries that need multiple agents."""
        from src.workflow.router import QueryRouter

        # Mock LLM to return multiple agents
        mock_llm.invoke.return_value = MagicMock(
            content='{"agents": ["market_analysis", "news_synthesizer"], "reasoning": "Query involves market data and news"}'
        )

        with patch('src.workflow.router.get_llm', return_value=mock_llm):
            router = QueryRouter()
            result = router.route("How is AAPL doing and what's the latest news?")

            # Should detect both market and news
            assert len(result["agents"]) >= 1

    def test_keyword_routing(self, mock_llm):
        """Test keyword-based routing."""
        from src.workflow.router import QueryRouter

        with patch('src.workflow.router.get_llm', return_value=mock_llm):
            router = QueryRouter()

            # Test various keyword patterns
            assert "portfolio_analysis" in router._keyword_route("analyze my portfolio")["agents"]
            assert "market_analysis" in router._keyword_route("stock price")["agents"]
            assert "goal_planning" in router._keyword_route("retirement planning")["agents"]
            assert "news_synthesizer" in router._keyword_route("latest news")["agents"]

    def test_query_type_detection(self, mock_llm):
        """Test query type detection."""
        from src.workflow.router import QueryRouter

        with patch('src.workflow.router.get_llm', return_value=mock_llm):
            router = QueryRouter()

            result = router.route("What is a mutual fund?")
            assert result["query_type"] in ["education", "general"]


class TestWorkflowGraph:
    """Tests for LangGraph workflow."""

    def test_workflow_init(self, mock_llm, sample_documents):
        """Test workflow initialization."""
        from src.workflow.graph import FinanceAssistantWorkflow
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.create_index(sample_documents, save=False)

        with patch('src.workflow.graph.get_llm', return_value=mock_llm):
            with patch('src.workflow.router.get_llm', return_value=mock_llm):
                with patch('src.agents.finance_qa_agent.get_llm', return_value=mock_llm):
                    with patch('src.agents.finance_qa_agent.get_vector_store', return_value=manager):
                        workflow = FinanceAssistantWorkflow()
                        assert workflow.graph is not None

    def test_workflow_run_education_query(self, mock_llm, sample_documents):
        """Test workflow execution for education query."""
        from src.workflow.graph import FinanceAssistantWorkflow
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.create_index(sample_documents, save=False)

        mock_llm.invoke.return_value = MagicMock(content="Stocks represent ownership in a company.")

        with patch('src.workflow.graph.get_llm', return_value=mock_llm):
            with patch('src.workflow.router.get_llm', return_value=mock_llm):
                with patch('src.agents.finance_qa_agent.get_llm', return_value=mock_llm):
                    with patch('src.agents.finance_qa_agent.get_vector_store', return_value=manager):
                        workflow = FinanceAssistantWorkflow()
                        result = workflow.run("What are stocks?")

                        assert "final_response" in result
                        assert result["final_response"] is not None

    def test_workflow_run_with_portfolio(self, mock_llm, sample_documents, sample_portfolio):
        """Test workflow execution with portfolio context."""
        from src.workflow.graph import FinanceAssistantWorkflow
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.create_index(sample_documents, save=False)

        mock_llm.invoke.return_value = MagicMock(content="Your portfolio is well diversified.")

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

    def test_workflow_error_handling(self, mock_llm, sample_documents):
        """Test workflow error handling."""
        from src.workflow.graph import FinanceAssistantWorkflow
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.create_index(sample_documents, save=False)

        # Make LLM raise an error
        mock_llm.invoke.side_effect = Exception("API Error")

        with patch('src.workflow.graph.get_llm', return_value=mock_llm):
            with patch('src.workflow.router.get_llm', return_value=mock_llm):
                with patch('src.agents.finance_qa_agent.get_llm', return_value=mock_llm):
                    with patch('src.agents.finance_qa_agent.get_vector_store', return_value=manager):
                        workflow = FinanceAssistantWorkflow()
                        result = workflow.run("What are stocks?")

                        # Should handle error gracefully
                        assert "errors" in result or "final_response" in result

    def test_workflow_state_management(self, mock_llm, sample_documents):
        """Test workflow state management."""
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
                        result = workflow.run("Test query", session_id="test-session")

                        assert result.get("session_id") == "test-session"


class TestResponseAggregator:
    """Tests for response aggregation."""

    def test_aggregate_single_response(self, mock_llm):
        """Test aggregating single agent response."""
        from src.workflow.graph import aggregate_responses

        agent_outputs = {
            "finance_qa": {
                "response": "Stocks represent ownership in a company.",
                "sources": ["basics.md"]
            }
        }

        result = aggregate_responses(agent_outputs, mock_llm)
        assert result is not None
        assert len(result) > 0

    def test_aggregate_multiple_responses(self, mock_llm):
        """Test aggregating multiple agent responses."""
        from src.workflow.graph import aggregate_responses

        agent_outputs = {
            "finance_qa": {
                "response": "Stocks represent ownership.",
                "sources": ["basics.md"]
            },
            "market_analysis": {
                "response": "AAPL is trading at $175.",
                "data": {"price": 175.0}
            }
        }

        mock_llm.invoke.return_value = MagicMock(
            content="Stocks represent ownership in companies. Apple (AAPL) is currently trading at $175."
        )

        result = aggregate_responses(agent_outputs, mock_llm)
        assert result is not None


class TestConditionalRouting:
    """Tests for conditional routing in workflow."""

    def test_select_agents_education(self, mock_llm, sample_documents):
        """Test agent selection for education queries."""
        from src.workflow.graph import FinanceAssistantWorkflow
        from src.core.state import create_initial_state
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.create_index(sample_documents, save=False)

        with patch('src.workflow.graph.get_llm', return_value=mock_llm):
            with patch('src.workflow.router.get_llm', return_value=mock_llm):
                with patch('src.agents.finance_qa_agent.get_llm', return_value=mock_llm):
                    with patch('src.agents.finance_qa_agent.get_vector_store', return_value=manager):
                        workflow = FinanceAssistantWorkflow()

                        state = create_initial_state("What is a bond?")
                        state["target_agents"] = ["finance_qa"]

                        next_nodes = workflow._select_agents(state)
                        assert "finance_qa" in next_nodes

    def test_select_agents_multiple(self, mock_llm, sample_documents):
        """Test agent selection for multi-agent queries."""
        from src.workflow.graph import FinanceAssistantWorkflow
        from src.core.state import create_initial_state
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.create_index(sample_documents, save=False)

        with patch('src.workflow.graph.get_llm', return_value=mock_llm):
            with patch('src.workflow.router.get_llm', return_value=mock_llm):
                with patch('src.agents.finance_qa_agent.get_llm', return_value=mock_llm):
                    with patch('src.agents.finance_qa_agent.get_vector_store', return_value=manager):
                        workflow = FinanceAssistantWorkflow()

                        state = create_initial_state("Tell me about stocks and check AAPL price")
                        state["target_agents"] = ["finance_qa", "market_analysis"]

                        next_nodes = workflow._select_agents(state)
                        assert len(next_nodes) >= 1
