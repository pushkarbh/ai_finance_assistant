"""
LangGraph workflow for multi-agent orchestration.
Coordinates agents to handle user queries with shared state.
"""

from typing import Any, Dict, List, Optional, Literal
import uuid

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
    Process a user query through the workflow.

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
