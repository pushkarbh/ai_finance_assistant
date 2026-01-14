"""
State management for LangGraph workflow.
Defines the shared state structure for multi-agent orchestration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage


class AgentType(str, Enum):
    """Available agent types in the system."""
    FINANCE_QA = "finance_qa"
    PORTFOLIO_ANALYSIS = "portfolio_analysis"
    MARKET_ANALYSIS = "market_analysis"
    GOAL_PLANNING = "goal_planning"
    NEWS_SYNTHESIZER = "news_synthesizer"
    ROUTER = "router"


class QueryType(str, Enum):
    """Types of user queries."""
    EDUCATION = "education"  # General financial education
    PORTFOLIO = "portfolio"  # Portfolio analysis
    MARKET = "market"  # Market data/analysis
    GOAL = "goal"  # Goal planning
    NEWS = "news"  # News synthesis
    MIXED = "mixed"  # Requires multiple agents


@dataclass
class PortfolioHolding:
    """Represents a single holding in a portfolio."""
    ticker: str
    shares: float
    purchase_price: Optional[float] = None
    purchase_date: Optional[str] = None
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    gain_loss: Optional[float] = None
    gain_loss_pct: Optional[float] = None


@dataclass
class Portfolio:
    """Represents a user's investment portfolio."""
    holdings: List[PortfolioHolding] = field(default_factory=list)
    total_value: float = 0.0
    total_cost: float = 0.0
    total_gain_loss: float = 0.0
    total_gain_loss_pct: float = 0.0
    allocation: Dict[str, float] = field(default_factory=dict)  # sector/type allocation


@dataclass
class FinancialGoal:
    """Represents a user's financial goal."""
    name: str
    target_amount: float
    current_amount: float = 0.0
    target_date: Optional[str] = None
    monthly_contribution: Optional[float] = None
    expected_return: float = 0.07  # Default 7%
    priority: int = 1


@dataclass
class MarketData:
    """Market data for a ticker."""
    ticker: str
    current_price: float
    change: float
    change_pct: float
    volume: Optional[int] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open_price: Optional[float] = None
    previous_close: Optional[float] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    timestamp: Optional[datetime] = None


class AgentState(TypedDict):
    """
    Shared state for LangGraph workflow.
    This state is passed between agents and updated throughout the conversation.
    """
    # Conversation
    messages: List[BaseMessage]  # Full conversation history
    current_query: str  # Current user query

    # Routing
    query_type: Optional[str]  # Classified query type
    target_agents: List[str]  # Agents to invoke for this query
    current_agent: Optional[str]  # Currently executing agent

    # Agent outputs
    agent_outputs: Dict[str, Any]  # Outputs from each agent
    final_response: Optional[str]  # Final synthesized response

    # Context data
    portfolio: Optional[Dict[str, Any]]  # User's portfolio if provided
    market_data: Dict[str, Any]  # Cached market data
    goals: List[Dict[str, Any]]  # User's financial goals

    # RAG context
    retrieved_context: List[str]  # Retrieved documents from knowledge base
    sources: List[Any]  # Sources used in response (can be strings or dicts with url/title)

    # Session info
    session_id: str
    user_id: Optional[str]

    # Error handling
    errors: List[str]

    # Metadata
    metadata: Dict[str, Any]


def create_initial_state(
    query: str,
    session_id: str,
    user_id: Optional[str] = None,
    portfolio: Optional[Dict[str, Any]] = None,
    goals: Optional[List[Dict[str, Any]]] = None
) -> AgentState:
    """
    Create an initial state for a new query.

    Args:
        query: The user's query
        session_id: Unique session identifier
        user_id: Optional user identifier
        portfolio: Optional portfolio data
        goals: Optional financial goals

    Returns:
        Initialized AgentState
    """
    return AgentState(
        messages=[],
        current_query=query,
        query_type=None,
        target_agents=[],
        current_agent=None,
        agent_outputs={},
        final_response=None,
        portfolio=portfolio,
        market_data={},
        goals=goals or [],
        retrieved_context=[],
        sources=[],
        session_id=session_id,
        user_id=user_id,
        errors=[],
        metadata={
            "start_time": datetime.now().isoformat(),
            "query_count": 0
        }
    )


def update_state_with_agent_output(
    state: AgentState,
    agent_name: str,
    output: Any,
    sources: Optional[List[Any]] = None
) -> AgentState:
    """
    Update state with output from an agent.

    Args:
        state: Current state
        agent_name: Name of the agent that produced output
        output: The agent's output
        sources: Optional list of sources used (strings or dicts)

    Returns:
        Updated state
    """
    state["agent_outputs"][agent_name] = output

    if sources:
        # For deduplication, we only add non-duplicate sources
        # For dicts, deduplicate by source/title key; for strings, by value
        existing_keys = set()
        for s in state["sources"]:
            if isinstance(s, dict):
                existing_keys.add(s.get("source", s.get("title", str(s))))
            else:
                existing_keys.add(str(s))

        for s in sources:
            if isinstance(s, dict):
                key = s.get("source", s.get("title", str(s)))
            else:
                key = str(s)

            if key not in existing_keys:
                state["sources"].append(s)
                existing_keys.add(key)

    return state


def add_error_to_state(state: AgentState, error: str) -> AgentState:
    """Add an error message to the state."""
    state["errors"].append(error)
    return state


def get_conversation_history(state: AgentState, max_messages: int = 10) -> List[BaseMessage]:
    """Get recent conversation history from state."""
    return state["messages"][-max_messages:]
