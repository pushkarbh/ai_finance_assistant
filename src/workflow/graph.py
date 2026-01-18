"""
LangGraph workflow for multi-agent orchestration.
Coordinates agents to handle user queries with shared state.
"""

from typing import Any, Dict, List, Optional, Literal
import uuid
import hashlib
import json
import time
import logging

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from src.core.state import AgentState, create_initial_state, add_error_to_state
from src.core.llm import get_llm
from src.core.guardrails import get_guardrails
from src.workflow.router import QueryRouter
from src.agents import (
    FinanceQAAgent,
    PortfolioAnalysisAgent,
    MarketAnalysisAgent,
    GoalPlanningAgent,
    NewsSynthesizerAgent
)

# Set up logger for cache debugging
logger = logging.getLogger(__name__)

# Track cache statistics
_CACHE_STATS = {"hits": 0, "misses": 0}


class FinanceAssistantWorkflow:
    """
    LangGraph-based workflow for the AI Finance Assistant.
    Orchestrates multiple specialized agents to handle user queries.
    """

    def __init__(self):
        """Initialize the workflow with all agents and router."""
        self.router = QueryRouter()
        self.guardrails = get_guardrails()

        # Initialize agents
        self.agents = {
            'finance_qa': FinanceQAAgent(),
            'portfolio_analysis': PortfolioAnalysisAgent(),
            'market_analysis': MarketAnalysisAgent(),
            'goal_planning': GoalPlanningAgent(),
            'news_synthesizer': NewsSynthesizerAgent()
        }

        self.llm = get_llm()

        # Build the graph
        self.graph = self._build_graph()
        self.app = self.graph.compile()

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.

        Returns:
            Configured StateGraph
        """
        # Create the graph with AgentState
        graph = StateGraph(AgentState)

        # Add nodes
        graph.add_node("route", self._route_node)
        graph.add_node("finance_qa", self._finance_qa_node)
        graph.add_node("portfolio_analysis", self._portfolio_analysis_node)
        graph.add_node("market_analysis", self._market_analysis_node)
        graph.add_node("goal_planning", self._goal_planning_node)
        graph.add_node("news_synthesizer", self._news_synthesizer_node)
        graph.add_node("synthesize", self._synthesize_node)

        # Set entry point
        graph.set_entry_point("route")

        # Add conditional edges from router
        graph.add_conditional_edges(
            "route",
            self._select_agents,
            {
                "finance_qa": "finance_qa",
                "portfolio_analysis": "portfolio_analysis",
                "market_analysis": "market_analysis",
                "goal_planning": "goal_planning",
                "news_synthesizer": "news_synthesizer",
                "synthesize": "synthesize"
            }
        )

        # Add edges from agents to synthesize
        for agent_name in self.agents.keys():
            graph.add_edge(agent_name, "synthesize")

        # Add edge from synthesize to end
        graph.add_edge("synthesize", END)

        return graph

    def _route_node(self, state: AgentState) -> AgentState:
        """
        Route the query to appropriate agents.

        Args:
            state: Current state

        Returns:
            Updated state with target agents
        """
        query = state["current_query"]

        # Route the query
        target_agents = self.router.route(query)
        query_type = self.router.classify_query_type(query)

        state["target_agents"] = target_agents
        state["query_type"] = query_type

        return state

    def _select_agents(self, state: AgentState) -> str:
        """
        Select which agent to run next based on routing.

        Args:
            state: Current state

        Returns:
            Next node name
        """
        target_agents = state.get("target_agents", [])

        if not target_agents:
            return "synthesize"

        # For simplicity, we'll run the first agent
        # A more complex implementation could run multiple in parallel
        current_agent = target_agents[0]
        state["current_agent"] = current_agent

        return current_agent

    def _finance_qa_node(self, state: AgentState) -> AgentState:
        """Run the Finance Q&A agent."""
        try:
            state = self.agents['finance_qa'].process(state)
        except Exception as e:
            state = add_error_to_state(state, f"Finance Q&A error: {str(e)}")
        return state

    def _portfolio_analysis_node(self, state: AgentState) -> AgentState:
        """Run the Portfolio Analysis agent."""
        try:
            state = self.agents['portfolio_analysis'].process(state)
        except Exception as e:
            state = add_error_to_state(state, f"Portfolio Analysis error: {str(e)}")
        return state

    def _market_analysis_node(self, state: AgentState) -> AgentState:
        """Run the Market Analysis agent."""
        try:
            state = self.agents['market_analysis'].process(state)
        except Exception as e:
            state = add_error_to_state(state, f"Market Analysis error: {str(e)}")
        return state

    def _goal_planning_node(self, state: AgentState) -> AgentState:
        """Run the Goal Planning agent."""
        try:
            state = self.agents['goal_planning'].process(state)
        except Exception as e:
            state = add_error_to_state(state, f"Goal Planning error: {str(e)}")
        return state

    def _news_synthesizer_node(self, state: AgentState) -> AgentState:
        """Run the News Synthesizer agent."""
        try:
            state = self.agents['news_synthesizer'].process(state)
        except Exception as e:
            state = add_error_to_state(state, f"News Synthesizer error: {str(e)}")
        return state

    def _synthesize_node(self, state: AgentState) -> AgentState:
        """
        Synthesize outputs from all agents into a final response.

        Args:
            state: Current state with agent outputs

        Returns:
            State with final response
        """
        agent_outputs = state.get("agent_outputs", {})

        if not agent_outputs:
            state["final_response"] = "I apologize, but I couldn't generate a response. Please try rephrasing your question."
            return state

        # If only one agent responded, use its output directly
        if len(agent_outputs) == 1:
            agent_name, output = list(agent_outputs.items())[0]
            response = output.get("response", "No response generated.")
            state["final_response"] = self._add_disclaimer(response)
            return state

        # Multiple agents - synthesize their outputs
        synthesis_parts = []
        for agent_name, output in agent_outputs.items():
            if "response" in output:
                synthesis_parts.append(f"From {agent_name}:\n{output['response']}")

        if synthesis_parts:
            combined = "\n\n---\n\n".join(synthesis_parts)

            # Use LLM to create a cohesive response
            synthesis_prompt = f"""Synthesize these responses from different financial experts into a single, cohesive response:

{combined}

Create a unified response that:
1. Combines relevant information from all sources
2. Avoids repetition
3. Maintains a beginner-friendly tone
4. Is well-organized with clear sections if needed"""

            messages = [HumanMessage(content=synthesis_prompt)]
            synthesized = self.llm.invoke(messages)
            state["final_response"] = self._add_disclaimer(synthesized.content)
        else:
            state["final_response"] = "I processed your query but couldn't generate a complete response."

        return state

    def _add_disclaimer(self, response: str) -> str:
        """Add educational disclaimer if not present."""
        disclaimer = "\n\n---\n*This information is for educational purposes only and should not be considered financial advice. Please consult a qualified financial advisor for personalized guidance.*"

        if "educational purposes" not in response.lower() and "not financial advice" not in response.lower():
            return response + disclaimer
        return response

    def run(
        self,
        query: str,
        session_id: Optional[str] = None,
        portfolio: Optional[Dict] = None,
        goals: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Run the workflow for a user query.

        Args:
            query: User's query
            session_id: Optional session ID
            portfolio: Optional portfolio data
            goals: Optional goals data

        Returns:
            Dict with response and metadata
        """
        # GUARDRAIL: Validate query before processing
        is_valid, refusal_message, classification = self.guardrails.validate_query(query)
        
        if not is_valid:
            # Return refusal message without processing
            return {
                "response": refusal_message,
                "sources": [],
                "agents_used": [],
                "agent_outputs": {},
                "query_type": "rejected",
                "classification": classification,
                "session_id": session_id or str(uuid.uuid4()),
                "errors": []
            }
        
        # Create initial state
        session_id = session_id or str(uuid.uuid4())
        initial_state = create_initial_state(
            query=query,
            session_id=session_id,
            portfolio=portfolio,
            goals=goals
        )

        # Add the query to messages
        initial_state["messages"] = [HumanMessage(content=query)]

        # Run the graph
        final_state = self.app.invoke(initial_state)

        # Extract results
        response = final_state.get("final_response", "")
        
        # GUARDRAIL: Validate response (add disclaimer if needed)
        _, validated_response = self.guardrails.validate_response(response)
        
        return {
            "response": validated_response,
            "sources": final_state.get("sources", []),
            "agents_used": list(final_state.get("agent_outputs", {}).keys()),
            "agent_outputs": final_state.get("agent_outputs", {}),
            "query_type": final_state.get("query_type"),
            "classification": "RELEVANT",
            "session_id": session_id,
            "errors": final_state.get("errors", [])
        }


# Singleton workflow instance
_workflow: Optional[FinanceAssistantWorkflow] = None


def get_workflow() -> FinanceAssistantWorkflow:
    """Get the singleton workflow instance."""
    global _workflow
    if _workflow is None:
        _workflow = FinanceAssistantWorkflow()
    return _workflow


def process_query(
    query: str,
    session_id: Optional[str] = None,
    portfolio: Optional[Dict] = None,
    goals: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Process a user query through the workflow with smart caching.

    Args:
        query: User's query
        session_id: Optional session ID
        portfolio: Optional portfolio data
        goals: Optional goals data

    Returns:
        Response dict with added metadata:
        - _cache_hit: bool (True if response was cached)
        - _response_time: float (time in seconds)
    """
    start_time = time.time()
    
    # Try to use cached version if Streamlit is available
    try:
        import streamlit as st
        
        # Check if this will be a cache hit by testing the cache key
        cache_key = _create_cache_key(query, portfolio, goals)
        
        # Call cached version
        cached_func = _get_cached_process_query()
        
        # Mark the start time before calling
        call_start = time.time()
        result = cached_func(query, session_id, portfolio, goals)
        call_duration = time.time() - call_start
        
        # If call was very fast (<100ms), it was likely cached
        is_cache_hit = call_duration < 0.1
        
        if is_cache_hit:
            _CACHE_STATS["hits"] += 1
            print(f"✅ CACHE HIT for query: '{query[:60]}...' ({call_duration*1000:.1f}ms)")
        else:
            _CACHE_STATS["misses"] += 1
            print(f"❌ CACHE MISS for query: '{query[:60]}...' ({call_duration:.2f}s)")
        
        # Add cache metadata to result
        if isinstance(result, dict):
            result['_cache_hit'] = is_cache_hit
            result['_response_time'] = call_duration
            result['_cache_stats'] = dict(_CACHE_STATS)
        
        return result
        
    except (ImportError, Exception) as e:
        # Fall back to direct execution if Streamlit not available
        print(f"⚠️ Cache not available, using direct execution: {e}")
        workflow = get_workflow()
        result = workflow.run(query, session_id, portfolio, goals)
        
        if isinstance(result, dict):
            result['_cache_hit'] = False
            result['_response_time'] = time.time() - start_time
        
        return result


def _get_cached_process_query():
    """
    Get the cached version of process_query, applying decorator lazily.
    This prevents Streamlit from being triggered at import time.
    """
    global _CACHED_FUNCTION
    if _CACHED_FUNCTION is None:
        import streamlit as st
        _CACHED_FUNCTION = st.cache_data(ttl=900, show_spinner=False)(_process_query_impl)
    return _CACHED_FUNCTION


# Global to hold the cached function
_CACHED_FUNCTION = None


def _process_query_impl(
    query: str,
    session_id: Optional[str] = None,
    portfolio: Optional[Dict] = None,
    goals: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Implementation of query processing (will be wrapped with cache decorator).
    
    Args:
        query: User's query
        session_id: Optional session ID
        portfolio: Optional portfolio data
        goals: Optional goals data
        
    Returns:
        Response dict
    """
    workflow = get_workflow()
    return workflow.run(query, session_id, portfolio, goals)


def _create_cache_key(query: str, portfolio: Optional[Dict], goals: Optional[List[Dict]]) -> str:
    """
    Create a unique cache key based on query, portfolio, and goals.
    
    Args:
        query: User's query
        portfolio: Portfolio data (if any)
        goals: Goals data (if any)
        
    Returns:
        MD5 hash as cache key
    """
    # Normalize query (lowercase, strip whitespace)
    normalized_query = query.lower().strip()
    
    # Create hash components
    components = [normalized_query]
    
    # Add portfolio hash if present
    if portfolio:
        # Sort keys for consistent hashing
        portfolio_str = json.dumps(portfolio, sort_keys=True)
        components.append(f"portfolio:{hashlib.md5(portfolio_str.encode()).hexdigest()[:8]}")
    
    # Add goals hash if present
    if goals:
        goals_str = json.dumps(goals, sort_keys=True)
        components.append(f"goals:{hashlib.md5(goals_str.encode()).hexdigest()[:8]}")
    
    # Combine all components
    cache_key = "|".join(components)
    return cache_key
