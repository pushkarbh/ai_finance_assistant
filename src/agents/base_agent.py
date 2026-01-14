"""
Base agent class for AI Finance Assistant.
Provides common functionality for all specialized agents.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.core.config import get_config
from src.core.llm import get_llm, AGENT_SYSTEM_PROMPTS
from src.core.state import AgentState


class BaseAgent(ABC):
    """
    Abstract base class for all finance assistant agents.
    Provides common functionality and interface for specialized agents.
    """

    def __init__(
        self,
        name: str,
        description: str,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize the base agent.

        Args:
            name: Agent name
            description: Agent description
            system_prompt: Custom system prompt (uses default if None)
        """
        self.name = name
        self.description = description
        self.config = get_config()
        self.llm = get_llm()

        # Get system prompt from defaults or use provided
        agent_key = name.lower().replace(" ", "_").replace("agent", "").strip("_")
        self.system_prompt = system_prompt or AGENT_SYSTEM_PROMPTS.get(
            agent_key,
            AGENT_SYSTEM_PROMPTS.get("finance_qa")  # Default fallback
        )

    @abstractmethod
    def process(self, state: AgentState) -> AgentState:
        """
        Process the current state and return updated state.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state
        """
        pass

    def generate_response(
        self,
        query: str,
        context: Optional[str] = None,
        conversation_history: Optional[List] = None
    ) -> str:
        """
        Generate a response using the LLM.

        Args:
            query: User's query
            context: Optional context from RAG or other sources
            conversation_history: Optional conversation history

        Returns:
            Generated response string
        """
        messages = [SystemMessage(content=self.system_prompt)]

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Build the prompt with context if available
        if context:
            prompt = f"""Context information:
{context}

User question: {query}

Please provide a helpful, educational response based on the context above."""
        else:
            prompt = query

        messages.append(HumanMessage(content=prompt))

        # Generate response
        response = self.llm.invoke(messages)
        return response.content

    def format_response_with_sources(
        self,
        response: str,
        sources: List[Any]
    ) -> str:
        """
        Format response with source citations.

        Args:
            response: Generated response
            sources: List of source strings or dicts with title/source/url

        Returns:
            Response with source citations appended
        """
        if not sources:
            return response

        sources_text = "\n\n---\n**Sources:**\n"
        for source in sources:
            if isinstance(source, dict):
                # Handle dict sources with URL
                title = source.get("title", source.get("source", "Unknown"))
                url = source.get("url")
                if url:
                    sources_text += f"- [{title}]({url})\n"
                else:
                    sources_text += f"- {title}\n"
            else:
                # Handle string sources
                sources_text += f"- {source}\n"

        return response + sources_text

    def add_disclaimer(self, response: str) -> str:
        """
        Add educational disclaimer to response.

        Args:
            response: Original response

        Returns:
            Response with disclaimer
        """
        disclaimer = "\n\n*This information is for educational purposes only and should not be considered financial advice. Please consult a qualified financial advisor for personalized guidance.*"

        # Only add if not already present
        if "educational purposes" not in response.lower():
            return response + disclaimer

        return response

    def extract_query_intent(self, query: str) -> Dict[str, Any]:
        """
        Extract intent and key information from a query.

        Args:
            query: User's query

        Returns:
            Dict with extracted intent information
        """
        # Use LLM to extract intent
        intent_prompt = f"""Analyze this financial query and extract:
1. Main topic (e.g., stocks, bonds, retirement, portfolio)
2. Query type (explanation, comparison, recommendation, calculation)
3. Key entities mentioned (tickers, amounts, dates)
4. User's apparent experience level (beginner, intermediate, advanced)

Query: {query}

Respond in this format:
TOPIC: <topic>
TYPE: <type>
ENTITIES: <comma-separated list>
EXPERIENCE: <level>"""

        messages = [
            SystemMessage(content="You are a query analysis assistant. Extract structured information from financial queries."),
            HumanMessage(content=intent_prompt)
        ]

        response = self.llm.invoke(messages)

        # Parse response
        intent = {
            "topic": "general",
            "type": "explanation",
            "entities": [],
            "experience": "beginner"
        }

        for line in response.content.split('\n'):
            if line.startswith("TOPIC:"):
                intent["topic"] = line.replace("TOPIC:", "").strip()
            elif line.startswith("TYPE:"):
                intent["type"] = line.replace("TYPE:", "").strip()
            elif line.startswith("ENTITIES:"):
                entities = line.replace("ENTITIES:", "").strip()
                intent["entities"] = [e.strip() for e in entities.split(",") if e.strip()]
            elif line.startswith("EXPERIENCE:"):
                intent["experience"] = line.replace("EXPERIENCE:", "").strip()

        return intent

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
