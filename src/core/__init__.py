"""
Core module for AI Finance Assistant.
Provides configuration, LLM integration, and state management.
"""

from src.core.config import (
    AppConfig,
    get_config,
    get_openai_api_key,
    get_alpha_vantage_api_key,
    load_config,
    reset_config
)

from src.core.llm import (
    LLMManager,
    get_llm,
    AGENT_SYSTEM_PROMPTS
)

from src.core.state import (
    AgentState,
    AgentType,
    QueryType,
    Portfolio,
    PortfolioHolding,
    FinancialGoal,
    MarketData,
    create_initial_state,
    update_state_with_agent_output,
    add_error_to_state,
    get_conversation_history
)

__all__ = [
    # Config
    "AppConfig",
    "get_config",
    "get_openai_api_key",
    "get_alpha_vantage_api_key",
    "load_config",
    "reset_config",
    # LLM
    "LLMManager",
    "get_llm",
    "AGENT_SYSTEM_PROMPTS",
    # State
    "AgentState",
    "AgentType",
    "QueryType",
    "Portfolio",
    "PortfolioHolding",
    "FinancialGoal",
    "MarketData",
    "create_initial_state",
    "update_state_with_agent_output",
    "add_error_to_state",
    "get_conversation_history",
]
