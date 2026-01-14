"""
Unit tests for the agents module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain_core.documents import Document


class TestBaseAgent:
    """Tests for BaseAgent class."""

    def test_base_agent_is_abstract(self):
        """Test that BaseAgent cannot be instantiated directly."""
        from src.agents.base_agent import BaseAgent

        with pytest.raises(TypeError):
            BaseAgent()

    def test_base_agent_subclass(self, mock_llm):
        """Test that BaseAgent can be subclassed."""
        from src.agents.base_agent import BaseAgent
        from src.core.state import AgentState

        class TestAgent(BaseAgent):
            @property
            def name(self) -> str:
                return "test_agent"

            @property
            def description(self) -> str:
                return "A test agent"

            def process(self, state: AgentState) -> AgentState:
                return state

        with patch('src.agents.base_agent.get_llm', return_value=mock_llm):
            agent = TestAgent()
            assert agent.name == "test_agent"
            assert agent.description == "A test agent"


class TestFinanceQAAgent:
    """Tests for Finance Q&A Agent."""

    def test_finance_qa_agent_init(self, mock_llm, sample_documents):
        """Test FinanceQAAgent initialization."""
        from src.agents.finance_qa_agent import FinanceQAAgent
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.create_index(sample_documents, save=False)

        with patch('src.agents.finance_qa_agent.get_llm', return_value=mock_llm):
            with patch('src.agents.finance_qa_agent.get_vector_store', return_value=manager):
                agent = FinanceQAAgent()
                assert agent.name == "finance_qa"

    def test_finance_qa_agent_process(self, mock_llm, sample_agent_state, sample_documents):
        """Test FinanceQAAgent processing."""
        from src.agents.finance_qa_agent import FinanceQAAgent
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.create_index(sample_documents, save=False)

        mock_llm.invoke.return_value = MagicMock(content="Stocks are ownership shares.")

        with patch('src.agents.finance_qa_agent.get_llm', return_value=mock_llm):
            with patch('src.agents.finance_qa_agent.get_vector_store', return_value=manager):
                agent = FinanceQAAgent()
                result = agent.process(sample_agent_state)

                assert "finance_qa" in result["agent_outputs"]
                assert "response" in result["agent_outputs"]["finance_qa"]


class TestPortfolioAgent:
    """Tests for Portfolio Analysis Agent."""

    def test_portfolio_agent_init(self, mock_llm):
        """Test PortfolioAgent initialization."""
        from src.agents.portfolio_agent import PortfolioAgent

        with patch('src.agents.portfolio_agent.get_llm', return_value=mock_llm):
            agent = PortfolioAgent()
            assert agent.name == "portfolio_analysis"

    def test_portfolio_agent_process_with_portfolio(self, mock_llm, sample_agent_state, sample_portfolio):
        """Test PortfolioAgent with portfolio data."""
        from src.agents.portfolio_agent import PortfolioAgent

        sample_agent_state["portfolio"] = sample_portfolio
        sample_agent_state["current_query"] = "Analyze my portfolio"

        mock_llm.invoke.return_value = MagicMock(content="Your portfolio is diversified.")

        with patch('src.agents.portfolio_agent.get_llm', return_value=mock_llm):
            with patch('src.agents.portfolio_agent.get_stock_price') as mock_price:
                mock_price.return_value = {"price": 175.0, "change_pct": 1.5}
                agent = PortfolioAgent()
                result = agent.process(sample_agent_state)

                assert "portfolio_analysis" in result["agent_outputs"]

    def test_portfolio_agent_process_no_portfolio(self, mock_llm, sample_agent_state):
        """Test PortfolioAgent without portfolio data."""
        from src.agents.portfolio_agent import PortfolioAgent

        sample_agent_state["portfolio"] = None
        sample_agent_state["current_query"] = "Analyze my portfolio"

        with patch('src.agents.portfolio_agent.get_llm', return_value=mock_llm):
            agent = PortfolioAgent()
            result = agent.process(sample_agent_state)

            assert "portfolio_analysis" in result["agent_outputs"]
            output = result["agent_outputs"]["portfolio_analysis"]
            assert "no portfolio" in output.get("response", "").lower() or "upload" in output.get("response", "").lower()

    def test_parse_csv_portfolio(self, mock_llm, csv_portfolio_content):
        """Test parsing CSV portfolio data."""
        from src.agents.portfolio_agent import PortfolioAgent

        with patch('src.agents.portfolio_agent.get_llm', return_value=mock_llm):
            agent = PortfolioAgent()
            portfolio = agent.parse_csv_portfolio(csv_portfolio_content)

            assert "holdings" in portfolio
            assert len(portfolio["holdings"]) == 4
            assert portfolio["holdings"][0]["ticker"] == "AAPL"

    def test_calculate_portfolio_metrics(self, mock_llm, sample_portfolio):
        """Test portfolio metrics calculation."""
        from src.agents.portfolio_agent import PortfolioAgent

        with patch('src.agents.portfolio_agent.get_llm', return_value=mock_llm):
            with patch('src.agents.portfolio_agent.get_stock_price') as mock_price:
                mock_price.return_value = {"price": 175.0}
                agent = PortfolioAgent()
                metrics = agent.calculate_metrics(sample_portfolio)

                assert "total_value" in metrics
                assert "holdings" in metrics


class TestMarketAgent:
    """Tests for Market Analysis Agent."""

    def test_market_agent_init(self, mock_llm):
        """Test MarketAgent initialization."""
        from src.agents.market_agent import MarketAgent

        with patch('src.agents.market_agent.get_llm', return_value=mock_llm):
            agent = MarketAgent()
            assert agent.name == "market_analysis"

    def test_market_agent_process(self, mock_llm, sample_agent_state, mock_market_summary):
        """Test MarketAgent processing."""
        from src.agents.market_agent import MarketAgent

        sample_agent_state["current_query"] = "How is the market doing?"

        mock_llm.invoke.return_value = MagicMock(content="The market is up today.")

        with patch('src.agents.market_agent.get_llm', return_value=mock_llm):
            with patch('src.agents.market_agent.get_market_summary', return_value=mock_market_summary):
                agent = MarketAgent()
                result = agent.process(sample_agent_state)

                assert "market_analysis" in result["agent_outputs"]

    def test_market_agent_stock_lookup(self, mock_llm, sample_agent_state, mock_stock_data):
        """Test MarketAgent stock lookup."""
        from src.agents.market_agent import MarketAgent

        sample_agent_state["current_query"] = "What is AAPL stock price?"

        mock_llm.invoke.return_value = MagicMock(content="Apple is trading at $175.50.")

        with patch('src.agents.market_agent.get_llm', return_value=mock_llm):
            with patch('src.agents.market_agent.get_stock_price', return_value=mock_stock_data):
                with patch('src.agents.market_agent.extract_tickers', return_value=["AAPL"]):
                    agent = MarketAgent()
                    result = agent.process(sample_agent_state)

                    assert "market_analysis" in result["agent_outputs"]


class TestGoalPlanningAgent:
    """Tests for Goal Planning Agent."""

    def test_goal_planning_agent_init(self, mock_llm):
        """Test GoalPlanningAgent initialization."""
        from src.agents.goal_planning_agent import GoalPlanningAgent

        with patch('src.agents.goal_planning_agent.get_llm', return_value=mock_llm):
            agent = GoalPlanningAgent()
            assert agent.name == "goal_planning"

    def test_goal_planning_agent_process(self, mock_llm, sample_agent_state, sample_goals):
        """Test GoalPlanningAgent processing."""
        from src.agents.goal_planning_agent import GoalPlanningAgent

        sample_agent_state["goals"] = sample_goals
        sample_agent_state["current_query"] = "How am I doing on my retirement goal?"

        mock_llm.invoke.return_value = MagicMock(content="You're on track for retirement.")

        with patch('src.agents.goal_planning_agent.get_llm', return_value=mock_llm):
            agent = GoalPlanningAgent()
            result = agent.process(sample_agent_state)

            assert "goal_planning" in result["agent_outputs"]

    def test_calculate_goal_projection(self, mock_llm):
        """Test goal projection calculation."""
        from src.agents.goal_planning_agent import GoalPlanningAgent

        goal = {
            "name": "Retirement",
            "target_amount": 1000000,
            "current_amount": 50000,
            "monthly_contribution": 1000,
            "expected_return": 0.07,
            "target_date": "2050-01-01"
        }

        with patch('src.agents.goal_planning_agent.get_llm', return_value=mock_llm):
            agent = GoalPlanningAgent()
            projection = agent.calculate_projection(goal)

            assert "projected_value" in projection
            assert "on_track" in projection
            assert projection["projected_value"] > goal["current_amount"]

    def test_calculate_required_contribution(self, mock_llm):
        """Test required contribution calculation."""
        from src.agents.goal_planning_agent import GoalPlanningAgent

        with patch('src.agents.goal_planning_agent.get_llm', return_value=mock_llm):
            agent = GoalPlanningAgent()
            required = agent.calculate_required_contribution(
                target_amount=100000,
                current_amount=20000,
                years=5,
                expected_return=0.07
            )

            assert required > 0


class TestNewsAgent:
    """Tests for News Synthesizer Agent."""

    def test_news_agent_init(self, mock_llm):
        """Test NewsAgent initialization."""
        from src.agents.news_agent import NewsAgent

        with patch('src.agents.news_agent.get_llm', return_value=mock_llm):
            agent = NewsAgent()
            assert agent.name == "news_synthesizer"

    def test_news_agent_process(self, mock_llm, sample_agent_state):
        """Test NewsAgent processing."""
        from src.agents.news_agent import NewsAgent

        sample_agent_state["current_query"] = "What's happening with tech stocks?"

        mock_llm.invoke.return_value = MagicMock(content="Tech stocks are volatile.")

        with patch('src.agents.news_agent.get_llm', return_value=mock_llm):
            with patch('src.agents.news_agent.get_stock_news') as mock_news:
                mock_news.return_value = [
                    {"title": "Tech Rally", "summary": "Tech stocks surge", "source": "Reuters"}
                ]
                agent = NewsAgent()
                result = agent.process(sample_agent_state)

                assert "news_synthesizer" in result["agent_outputs"]

    def test_news_agent_extract_topics(self, mock_llm):
        """Test extracting topics from query."""
        from src.agents.news_agent import NewsAgent

        with patch('src.agents.news_agent.get_llm', return_value=mock_llm):
            agent = NewsAgent()
            topics = agent.extract_topics("What's happening with Apple and Microsoft?")

            # Should extract company names or general market topics
            assert isinstance(topics, list)


class TestAgentRegistry:
    """Tests for agent registry functions."""

    def test_get_agent_by_name(self, mock_llm, sample_documents):
        """Test getting agent by name."""
        from src.agents import get_agent
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.create_index(sample_documents, save=False)

        with patch('src.agents.finance_qa_agent.get_llm', return_value=mock_llm):
            with patch('src.agents.finance_qa_agent.get_vector_store', return_value=manager):
                agent = get_agent("finance_qa")
                assert agent is not None
                assert agent.name == "finance_qa"

    def test_get_agent_invalid_name(self):
        """Test getting agent with invalid name."""
        from src.agents import get_agent

        agent = get_agent("invalid_agent_name")
        assert agent is None

    def test_get_all_agents(self, mock_llm, sample_documents):
        """Test getting all agents."""
        from src.agents import get_all_agents
        from src.rag.vector_store import VectorStoreManager

        manager = VectorStoreManager()
        manager.create_index(sample_documents, save=False)

        with patch('src.agents.finance_qa_agent.get_llm', return_value=mock_llm):
            with patch('src.agents.portfolio_agent.get_llm', return_value=mock_llm):
                with patch('src.agents.market_agent.get_llm', return_value=mock_llm):
                    with patch('src.agents.goal_planning_agent.get_llm', return_value=mock_llm):
                        with patch('src.agents.news_agent.get_llm', return_value=mock_llm):
                            with patch('src.agents.finance_qa_agent.get_vector_store', return_value=manager):
                                agents = get_all_agents()
                                assert len(agents) >= 5
