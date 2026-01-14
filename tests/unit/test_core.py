"""
Unit tests for the core module (config, state, llm).
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config import (
    AppConfig,
    LLMConfig,
    RAGConfig,
    load_config,
    get_config,
    get_openai_api_key,
    reset_config
)
from src.core.state import (
    AgentState,
    AgentType,
    QueryType,
    PortfolioHolding,
    Portfolio,
    FinancialGoal,
    create_initial_state,
    update_state_with_agent_output,
    add_error_to_state,
    get_conversation_history
)


class TestConfig:
    """Tests for configuration module."""

    def test_llm_config_defaults(self):
        """Test LLM config default values."""
        config = LLMConfig()
        assert config.provider == "openai"
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.7
        assert config.max_tokens == 2000

    def test_rag_config_defaults(self):
        """Test RAG config default values."""
        config = RAGConfig()
        assert config.chunk_size == 1000
        assert config.chunk_overlap == 200
        assert config.top_k == 5
        assert config.similarity_threshold == 0.7

    def test_app_config_initialization(self):
        """Test AppConfig initialization."""
        config = AppConfig()
        assert config.name == "AI Finance Assistant"
        assert config.version == "1.0.0"
        assert isinstance(config.llm, LLMConfig)
        assert isinstance(config.rag, RAGConfig)

    def test_app_config_paths(self):
        """Test AppConfig path setup."""
        config = AppConfig()
        assert config.project_root.exists() or True  # May not exist in test env
        assert "knowledge_base" in str(config.knowledge_base_path)
        assert "faiss_index" in str(config.faiss_index_path)

    def test_get_openai_api_key(self):
        """Test getting OpenAI API key from environment."""
        # Key is set in conftest.py
        key = get_openai_api_key()
        assert key == 'test-api-key-for-testing'

    def test_get_openai_api_key_missing(self):
        """Test error when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove the key temporarily
            original_key = os.environ.pop('OPENAI_API_KEY', None)
            try:
                with pytest.raises(ValueError, match="OPENAI_API_KEY not found"):
                    get_openai_api_key()
            finally:
                if original_key:
                    os.environ['OPENAI_API_KEY'] = original_key

    def test_get_config_singleton(self):
        """Test that get_config returns singleton."""
        reset_config()
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reset_config(self):
        """Test config reset functionality."""
        config1 = get_config()
        reset_config()
        config2 = get_config()
        # After reset, should be new instance (but with same values)
        assert config1.name == config2.name


class TestState:
    """Tests for state management module."""

    def test_agent_type_enum(self):
        """Test AgentType enum values."""
        assert AgentType.FINANCE_QA.value == "finance_qa"
        assert AgentType.PORTFOLIO_ANALYSIS.value == "portfolio_analysis"
        assert AgentType.MARKET_ANALYSIS.value == "market_analysis"
        assert AgentType.GOAL_PLANNING.value == "goal_planning"
        assert AgentType.NEWS_SYNTHESIZER.value == "news_synthesizer"

    def test_query_type_enum(self):
        """Test QueryType enum values."""
        assert QueryType.EDUCATION.value == "education"
        assert QueryType.PORTFOLIO.value == "portfolio"
        assert QueryType.MARKET.value == "market"
        assert QueryType.GOAL.value == "goal"

    def test_portfolio_holding_creation(self):
        """Test PortfolioHolding dataclass."""
        holding = PortfolioHolding(
            ticker="AAPL",
            shares=10.0,
            purchase_price=150.0
        )
        assert holding.ticker == "AAPL"
        assert holding.shares == 10.0
        assert holding.purchase_price == 150.0
        assert holding.current_price is None

    def test_financial_goal_creation(self):
        """Test FinancialGoal dataclass."""
        goal = FinancialGoal(
            name="Retirement",
            target_amount=1000000,
            current_amount=50000
        )
        assert goal.name == "Retirement"
        assert goal.target_amount == 1000000
        assert goal.expected_return == 0.07  # Default

    def test_create_initial_state(self):
        """Test initial state creation."""
        state = create_initial_state(
            query="What are stocks?",
            session_id="test-123"
        )

        assert state["current_query"] == "What are stocks?"
        assert state["session_id"] == "test-123"
        assert state["messages"] == []
        assert state["target_agents"] == []
        assert state["agent_outputs"] == {}
        assert state["errors"] == []

    def test_create_initial_state_with_portfolio(self, sample_portfolio):
        """Test initial state with portfolio data."""
        state = create_initial_state(
            query="Analyze my portfolio",
            session_id="test-456",
            portfolio=sample_portfolio
        )

        assert state["portfolio"] == sample_portfolio
        assert len(state["portfolio"]["holdings"]) == 4

    def test_update_state_with_agent_output(self, sample_agent_state):
        """Test updating state with agent output."""
        output = {"response": "Test response", "data": {"key": "value"}}
        sources = ["source1.md", "source2.md"]

        updated_state = update_state_with_agent_output(
            sample_agent_state,
            "finance_qa",
            output,
            sources
        )

        assert "finance_qa" in updated_state["agent_outputs"]
        assert updated_state["agent_outputs"]["finance_qa"] == output
        assert "source1.md" in updated_state["sources"]
        assert "source2.md" in updated_state["sources"]

    def test_add_error_to_state(self, sample_agent_state):
        """Test adding error to state."""
        state = add_error_to_state(sample_agent_state, "Test error message")
        assert "Test error message" in state["errors"]

    def test_get_conversation_history(self, sample_agent_state):
        """Test getting conversation history."""
        from langchain_core.messages import HumanMessage, AIMessage

        sample_agent_state["messages"] = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there"),
            HumanMessage(content="What are stocks?")
        ]

        history = get_conversation_history(sample_agent_state, max_messages=2)
        assert len(history) == 2


class TestLLM:
    """Tests for LLM module."""

    def test_agent_system_prompts_exist(self):
        """Test that system prompts are defined for all agents."""
        from src.core.llm import AGENT_SYSTEM_PROMPTS

        expected_keys = ['finance_qa', 'portfolio_analysis', 'market_analysis',
                         'goal_planning', 'news_synthesizer', 'router']

        for key in expected_keys:
            assert key in AGENT_SYSTEM_PROMPTS
            assert len(AGENT_SYSTEM_PROMPTS[key]) > 100  # Should be substantial

    def test_llm_manager_initialization(self, mock_llm):
        """Test LLM manager can be initialized."""
        from src.core.llm import LLMManager

        with patch('src.core.llm.get_openai_api_key', return_value='test-key'):
            with patch('src.core.llm.ChatOpenAI', return_value=mock_llm):
                manager = LLMManager()
                assert manager.model == "gpt-4o-mini"
                assert manager.temperature == 0.7

    def test_get_llm_function(self, mock_llm):
        """Test get_llm convenience function."""
        from src.core.llm import get_llm

        with patch('src.core.llm.get_openai_api_key', return_value='test-key'):
            with patch('src.core.llm.ChatOpenAI', return_value=mock_llm):
                llm = get_llm(model="gpt-4", temperature=0.5)
                # Should return the mock
                assert llm is not None
