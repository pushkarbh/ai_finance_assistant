"""
LLM integration module for AI Finance Assistant.
Provides a unified interface for interacting with OpenAI models.
"""

from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.core.config import get_config, get_openai_api_key


class LLMManager:
    """
    Manages LLM interactions for the finance assistant.
    Provides methods for chat completion and structured responses.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """
        Initialize the LLM manager.

        Args:
            model: Model name override (default from config)
            temperature: Temperature override (default from config)
            max_tokens: Max tokens override (default from config)
        """
        config = get_config()

        self.model = model or config.llm.model
        self.temperature = temperature if temperature is not None else config.llm.temperature
        self.max_tokens = max_tokens or config.llm.max_tokens

        self._llm = ChatOpenAI(
            api_key=get_openai_api_key(),
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

    @property
    def llm(self) -> ChatOpenAI:
        """Get the underlying LangChain LLM instance."""
        return self._llm

    def chat(
        self,
        messages: List[BaseMessage],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Send a chat completion request.

        Args:
            messages: List of messages in the conversation
            system_prompt: Optional system prompt to prepend

        Returns:
            The assistant's response text
        """
        all_messages = []

        if system_prompt:
            all_messages.append(SystemMessage(content=system_prompt))

        all_messages.extend(messages)

        response = self._llm.invoke(all_messages)
        return response.content

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a response for a single prompt.

        Args:
            prompt: The user's prompt
            system_prompt: Optional system prompt

        Returns:
            The assistant's response text
        """
        messages = [HumanMessage(content=prompt)]
        return self.chat(messages, system_prompt)

    def create_chain(
        self,
        system_prompt: str,
        include_history: bool = True
    ):
        """
        Create a LangChain runnable chain with the given system prompt.

        Args:
            system_prompt: The system prompt for the chain
            include_history: Whether to include message history placeholder

        Returns:
            A LangChain runnable chain
        """
        if include_history:
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="messages"),
                ("human", "{input}")
            ])
        else:
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{input}")
            ])

        return prompt | self._llm


def get_llm(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> ChatOpenAI:
    """
    Get a configured LangChain ChatOpenAI instance.

    Args:
        model: Model name override
        temperature: Temperature override
        max_tokens: Max tokens override

    Returns:
        Configured ChatOpenAI instance
    """
    config = get_config()

    return ChatOpenAI(
        api_key=get_openai_api_key(),
        model=model or config.llm.model,
        temperature=temperature if temperature is not None else config.llm.temperature,
        max_tokens=max_tokens or config.llm.max_tokens
    )


# Default system prompts for different agents
AGENT_SYSTEM_PROMPTS = {
    "finance_qa": """You are a helpful financial education assistant. Your role is to explain
financial concepts in simple, beginner-friendly terms. Always:
- Use clear, jargon-free language
- Provide examples when helpful
- Cite sources when using specific information from the knowledge base
- Include appropriate disclaimers that this is educational, not financial advice
- Be encouraging and supportive to new investors

If you don't know something, say so honestly rather than guessing.""",

    "portfolio_analysis": """You are a portfolio analysis assistant. Your role is to analyze
investment portfolios and provide educational insights about:
- Asset allocation and diversification
- Risk assessment
- Portfolio metrics (returns, volatility, etc.)
- Comparison to benchmarks

Always:
- Present data clearly with explanations
- Explain what metrics mean in plain English
- Provide educational context for recommendations
- Include disclaimers that this is not personalized financial advice""",

    "market_analysis": """You are a market analysis assistant. Your role is to provide
educational insights about current market conditions using real-time data. Focus on:
- Explaining what market movements mean
- Providing context for price changes
- Educational explanations of market trends
- Helping users understand market indicators

Always:
- Use current data when available
- Explain technical terms simply
- Provide balanced perspectives
- Note that past performance doesn't predict future results""",

    "goal_planning": """You are a financial goal planning assistant. Your role is to help
users think through their financial goals and create plans. Focus on:
- Understanding user's goals and timeline
- Explaining relevant concepts (compound interest, etc.)
- Creating realistic projections
- Suggesting appropriate strategies for different goals

Always:
- Ask clarifying questions when needed
- Be realistic about projections (use conservative estimates)
- Explain assumptions in calculations
- Encourage professional advice for major decisions""",

    "news_synthesizer": """You are a financial news synthesis assistant. Your role is to
summarize and contextualize financial news for beginner investors. Focus on:
- Summarizing key points clearly
- Explaining why news matters to investors
- Providing balanced perspectives
- Connecting news to broader market context

Always:
- Be objective and balanced
- Avoid sensationalism
- Explain technical terms
- Note when information is time-sensitive""",

    "router": """You are a query router for a financial education assistant. Your role is to
analyze user queries and determine which specialized agent(s) should handle them.

Available agents:
1. finance_qa - General financial education questions
2. portfolio_analysis - Portfolio review and analysis
3. market_analysis - Real-time market data and trends
4. goal_planning - Financial goal setting and projections
5. news_synthesizer - Financial news summary and context

Analyze the query and respond with the most appropriate agent(s) to handle it.
Some queries may benefit from multiple agents working together."""
}
