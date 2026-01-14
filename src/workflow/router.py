"""
Query Router for the LangGraph workflow.
Classifies user queries and determines which agent(s) should handle them.
"""

from typing import List, Tuple
from enum import Enum

from langchain_core.messages import HumanMessage, SystemMessage

from src.core.llm import get_llm
from src.core.state import AgentState, AgentType


class QueryRouter:
    """
    Routes user queries to appropriate agents based on content analysis.
    Uses LLM to classify queries and determine routing.
    """

    ROUTING_PROMPT = """You are a query router for a financial education assistant. Analyze the user's query and determine which specialized agent(s) should handle it.

Available agents:
1. finance_qa - General financial education questions (what is X, explain Y, how does Z work)
2. portfolio_analysis - Portfolio review, holdings analysis, allocation questions
3. market_analysis - Real-time market data, stock prices, market trends
4. goal_planning - Financial goals, retirement planning, savings projections
5. news_synthesizer - Financial news, market events, recent developments

Rules:
- Choose the MOST relevant agent(s) for the query
- Some queries may need multiple agents (e.g., "analyze my portfolio and suggest goals")
- If uncertain, default to finance_qa
- Maximum 3 agents per query

Respond with ONLY the agent names, comma-separated, in order of relevance.
Example responses:
- "finance_qa"
- "portfolio_analysis, market_analysis"
- "goal_planning, finance_qa"

User query: {query}

Agents to use:"""

    def __init__(self):
        """Initialize the query router."""
        self.llm = get_llm(temperature=0)  # Low temperature for consistent routing

    def route(self, query: str) -> List[str]:
        """
        Route a query to appropriate agents.

        Args:
            query: User's query

        Returns:
            List of agent names to invoke
        """
        # First, try keyword-based routing for common patterns
        keyword_route = self._keyword_route(query)
        if keyword_route:
            return keyword_route

        # Use LLM for more complex routing
        return self._llm_route(query)

    def _keyword_route(self, query: str) -> List[str]:
        """
        Fast keyword-based routing for common patterns.

        Args:
            query: User's query

        Returns:
            List of agents or None if no keyword match
        """
        query_lower = query.lower()

        # Portfolio keywords
        portfolio_keywords = ['portfolio', 'holdings', 'allocation', 'diversif', 'my stocks', 'my investments']
        if any(kw in query_lower for kw in portfolio_keywords):
            if 'goal' in query_lower or 'retire' in query_lower:
                return ['portfolio_analysis', 'goal_planning']
            return ['portfolio_analysis']

        # Market/Price keywords
        market_keywords = ['price', 'stock price', 'how is', "how's", 'market today', 'trading at', 'current price']
        ticker_patterns = ['$', 'aapl', 'msft', 'googl', 'amzn', 'tsla', 'spy', 'qqq']
        if any(kw in query_lower for kw in market_keywords) or any(tp in query_lower for tp in ticker_patterns):
            return ['market_analysis']

        # Goal/Planning keywords
        goal_keywords = ['goal', 'retire', 'save for', 'saving for', 'plan', 'projection', 'how much', 'how long', 'afford']
        if any(kw in query_lower for kw in goal_keywords):
            return ['goal_planning']

        # News keywords
        news_keywords = ['news', 'headline', 'recent', 'today', 'happened', 'event', 'announcement']
        if any(kw in query_lower for kw in news_keywords):
            return ['news_synthesizer']

        # Educational keywords - default to finance_qa
        education_keywords = ['what is', 'what are', 'explain', 'how does', 'difference between', 'tell me about', 'learn', 'understand']
        if any(kw in query_lower for kw in education_keywords):
            return ['finance_qa']

        return None  # No keyword match, use LLM routing

    def _llm_route(self, query: str) -> List[str]:
        """
        Use LLM for query routing.

        Args:
            query: User's query

        Returns:
            List of agent names
        """
        prompt = self.ROUTING_PROMPT.format(query=query)

        messages = [
            SystemMessage(content="You are a query classification assistant. Respond only with agent names."),
            HumanMessage(content=prompt)
        ]

        response = self.llm.invoke(messages)
        agents_str = response.content.strip().lower()

        # Parse response
        agents = [a.strip() for a in agents_str.split(',')]

        # Validate agent names
        valid_agents = ['finance_qa', 'portfolio_analysis', 'market_analysis', 'goal_planning', 'news_synthesizer']
        agents = [a for a in agents if a in valid_agents]

        # Default to finance_qa if nothing valid
        if not agents:
            agents = ['finance_qa']

        return agents[:3]  # Max 3 agents

    def classify_query_type(self, query: str) -> str:
        """
        Classify the type of query.

        Args:
            query: User's query

        Returns:
            Query type string
        """
        query_lower = query.lower()

        if '?' in query:
            if any(kw in query_lower for kw in ['what', 'how', 'why', 'explain']):
                return 'educational'
            elif any(kw in query_lower for kw in ['should', 'recommend', 'suggest']):
                return 'advisory'
            elif any(kw in query_lower for kw in ['price', 'cost', 'worth']):
                return 'data_request'

        if any(kw in query_lower for kw in ['analyze', 'review', 'check']):
            return 'analysis'

        if any(kw in query_lower for kw in ['calculate', 'project', 'estimate']):
            return 'calculation'

        if any(kw in query_lower for kw in ['compare', 'versus', 'vs', 'difference']):
            return 'comparison'

        return 'general'


def route_query(query: str) -> List[str]:
    """
    Convenience function to route a query.

    Args:
        query: User's query

    Returns:
        List of agent names
    """
    router = QueryRouter()
    return router.route(query)
