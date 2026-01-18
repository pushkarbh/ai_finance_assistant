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
        graph.add_node("process_agents", self._process_agents_node)
        graph.add_node("finance_qa", self._finance_qa_node)
        graph.add_node("portfolio_analysis", self._portfolio_analysis_node)
        graph.add_node("market_analysis", self._market_analysis_node)
        graph.add_node("goal_planning", self._goal_planning_node)
        graph.add_node("news_synthesizer", self._news_synthesizer_node)
        graph.add_node("check_remaining", self._check_remaining_node)
        graph.add_node("synthesize", self._synthesize_node)

        # Set entry point
        graph.set_entry_point("route")

        # Route goes to process_agents which handles sequential execution
        graph.add_edge("route", "process_agents")

        # Process_agents selects next agent to run
        graph.add_conditional_edges(
            "process_agents",
            self._select_next_agent,
            {
                "finance_qa": "finance_qa",
                "portfolio_analysis": "portfolio_analysis",
                "market_analysis": "market_analysis",
                "goal_planning": "goal_planning",
                "news_synthesizer": "news_synthesizer",
                "synthesize": "synthesize"
            }
        )

        # All agents go to check_remaining to see if more agents needed
        for agent_name in self.agents.keys():
            graph.add_edge(agent_name, "check_remaining")

        # Check_remaining either loops back to process_agents or goes to synthesize
        graph.add_conditional_edges(
            "check_remaining",
            self._check_more_agents,
            {
                "process_agents": "process_agents",
                "synthesize": "synthesize"
            }
        )

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
        state["processed_agents"] = []  # Track which agents have been processed

        return state

    def _process_agents_node(self, state: AgentState) -> AgentState:
        """
        Prepare to process the next agent.
        
        Args:
            state: Current state
            
        Returns:
            Updated state
        """
        # This node just passes through to allow conditional routing
        return state

    def _select_next_agent(self, state: AgentState) -> str:
        """
        Select which agent to run next based on routing.

        Args:
            state: Current state

        Returns:
            Next node name
        """
        target_agents = state.get("target_agents", [])
        processed_agents = state.get("processed_agents", [])

        # Find next unprocessed agent
        remaining_agents = [a for a in target_agents if a not in processed_agents]

        if not remaining_agents:
            return "synthesize"

        # Return the first remaining agent
        next_agent = remaining_agents[0]
        state["current_agent"] = next_agent

        return next_agent

    def _check_remaining_node(self, state: AgentState) -> AgentState:
        """
        Mark current agent as processed.
        
        Args:
            state: Current state
            
        Returns:
            Updated state
        """
        current_agent = state.get("current_agent")
        if current_agent:
            processed = state.get("processed_agents", [])
            if current_agent not in processed:
                processed.append(current_agent)
                state["processed_agents"] = processed
        
        return state

    def _check_more_agents(self, state: AgentState) -> str:
        """
        Check if there are more agents to process.
        
        Args:
            state: Current state
            
        Returns:
            Next node name
        """
        target_agents = state.get("target_agents", [])
        processed_agents = state.get("processed_agents", [])
        
        remaining = [a for a in target_agents if a not in processed_agents]
        
        if remaining:
            return "process_agents"
        else:
            return "synthesize"

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
        # Create a cohesive narrative that combines insights
        synthesis_parts = []
        agent_names = list(agent_outputs.keys())
        
        for agent_name, output in agent_outputs.items():
            if "response" in output:
                # Add section header based on agent type
                section_title = {
                    'portfolio_analysis': '📊 Portfolio Analysis',
                    'goal_planning': '🎯 Financial Planning & Goals',
                    'market_analysis': '📈 Market Insights',
                    'finance_qa': '💡 Financial Education',
                    'news_synthesizer': '📰 Recent Market News'
                }.get(agent_name, agent_name.replace('_', ' ').title())
                
                synthesis_parts.append(f"## {section_title}\n\n{output['response']}")

        if synthesis_parts:
            # If we have multiple agents, use LLM to create a cohesive narrative
            combined = "\n\n---\n\n".join(synthesis_parts)

            synthesis_prompt = f"""You are synthesizing insights from multiple financial analysis agents into a single, cohesive response for a user.

The user received analysis from {len(agent_outputs)} specialized agents: {', '.join(agent_names)}.

Here are their individual responses:

{combined}

Create a unified, well-structured response that:
1. Starts with a brief overview connecting the different analyses
2. Presents each agent's insights in clear, distinct sections with the headers provided
3. Highlights important connections between the analyses (e.g., how portfolio performance relates to retirement goals)
4. Maintains a helpful, educational tone suitable for beginners
5. Ends with clear, actionable next steps or recommendations that tie everything together
6. Keep all specific numbers, percentages, and data points from the original responses

Format with markdown headers (##) for each section. Make it read as one coherent advisory session, not separate disconnected reports."""

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
        return {
            "response": final_state.get("final_response", ""),
            "sources": final_state.get("sources", []),
            "agents_used": list(final_state.get("agent_outputs", {}).keys()),
            "agent_outputs": final_state.get("agent_outputs", {}),
            "query_type": final_state.get("query_type"),
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
