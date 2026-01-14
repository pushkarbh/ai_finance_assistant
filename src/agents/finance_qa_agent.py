"""
Finance Q&A Agent for AI Finance Assistant.
Handles general financial education queries using RAG.
"""

from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, AIMessage

from src.agents.base_agent import BaseAgent
from src.core.state import AgentState, update_state_with_agent_output
from src.core.llm import AGENT_SYSTEM_PROMPTS
from src.rag.retriever import FinanceRetriever, RAGChain


class FinanceQAAgent(BaseAgent):
    """
    Finance Q&A Agent using RAG for educational responses.
    Retrieves relevant information from the knowledge base to answer questions.
    """

    def __init__(
        self,
        top_k: int = 5,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize the Finance Q&A Agent.

        Args:
            top_k: Number of documents to retrieve
            system_prompt: Custom system prompt
        """
        super().__init__(
            name="Finance Q&A Agent",
            description="Handles general financial education queries using RAG",
            system_prompt=system_prompt or AGENT_SYSTEM_PROMPTS["finance_qa"]
        )

        self.top_k = top_k
        self.retriever = FinanceRetriever(top_k=top_k)
        self.rag_chain = RAGChain(retriever=self.retriever, top_k=top_k)

    def process(self, state: AgentState) -> AgentState:
        """
        Process the query using RAG and generate a response.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state with response
        """
        query = state["current_query"]

        # Get context from RAG
        rag_result = self.rag_chain.get_context(query)
        context = rag_result["context"]
        sources = rag_result["sources"]

        # Store retrieved context in state
        state["retrieved_context"] = [context] if context else []

        # Generate response
        response = self.answer_question(query, context)

        # Add full source info to state (includes URLs for citations)
        state["sources"].extend(sources)

        # Format with sources if available (now passes full source dicts with URLs)
        if sources:
            response = self.format_response_with_sources(response, sources)

        # Update state with output
        state = update_state_with_agent_output(
            state,
            "finance_qa",
            {
                "response": response,
                "sources": sources,
                "num_sources": len(sources)
            },
            [s.get("source", s.get("title", "Unknown")) for s in sources]
        )

        return state

    def answer_question(
        self,
        question: str,
        context: Optional[str] = None
    ) -> str:
        """
        Answer a financial education question.

        Args:
            question: User's question
            context: Retrieved context from knowledge base

        Returns:
            Educational answer
        """
        if context:
            prompt = f"""Based on the following information from our financial knowledge base, please answer the user's question in a clear, educational manner suitable for beginners.

KNOWLEDGE BASE CONTEXT:
{context}

USER QUESTION: {question}

Please provide:
1. A clear, jargon-free explanation
2. Examples if helpful
3. Key takeaways

If the context doesn't fully answer the question, acknowledge this and provide what information you can. Always maintain an encouraging, educational tone."""
        else:
            prompt = f"""Please answer this financial education question in a clear, beginner-friendly manner:

{question}

Provide a helpful explanation with examples if relevant. Note that this response is based on general knowledge rather than specific knowledge base content."""

        return self.generate_response(prompt)

    def explain_concept(self, concept: str) -> str:
        """
        Explain a financial concept in beginner-friendly terms.

        Args:
            concept: Financial concept to explain

        Returns:
            Educational explanation
        """
        # Retrieve relevant context
        rag_result = self.rag_chain.get_context(f"What is {concept}? Explain {concept}")
        context = rag_result["context"]

        prompt = f"""Explain the financial concept "{concept}" to someone who is new to investing.

CONTEXT:
{context}

Please provide:
1. A simple definition
2. Why it matters to investors
3. A real-world example
4. Common misconceptions (if any)

Keep the explanation clear and jargon-free."""

        return self.generate_response(prompt)

    def compare_concepts(self, concept1: str, concept2: str) -> str:
        """
        Compare two financial concepts.

        Args:
            concept1: First concept
            concept2: Second concept

        Returns:
            Comparison explanation
        """
        # Retrieve context for both concepts
        context1 = self.rag_chain.get_context(concept1)["context"]
        context2 = self.rag_chain.get_context(concept2)["context"]

        combined_context = f"About {concept1}:\n{context1}\n\nAbout {concept2}:\n{context2}"

        prompt = f"""Compare {concept1} and {concept2} for a beginner investor.

CONTEXT:
{combined_context}

Please provide:
1. Brief explanation of each
2. Key similarities
3. Key differences
4. When to use/consider each
5. A simple comparison table if helpful"""

        return self.generate_response(prompt)

    def answer_with_examples(
        self,
        question: str,
        num_examples: int = 2
    ) -> str:
        """
        Answer a question with practical examples.

        Args:
            question: User's question
            num_examples: Number of examples to include

        Returns:
            Answer with examples
        """
        rag_result = self.rag_chain.get_context(question)
        context = rag_result["context"]

        prompt = f"""Answer this financial question with {num_examples} practical examples:

QUESTION: {question}

CONTEXT:
{context}

Please provide:
1. A clear answer to the question
2. {num_examples} concrete examples with numbers
3. Key takeaways

Make the examples realistic and relatable to everyday investors."""

        return self.generate_response(prompt)

    def get_related_topics(self, topic: str) -> List[str]:
        """
        Get related topics for further learning.

        Args:
            topic: Current topic

        Returns:
            List of related topics
        """
        prompt = f"""Given the financial topic "{topic}", suggest 5 related topics that a beginner investor might want to learn about next.

Return only the topic names, one per line, without numbering or explanations."""

        response = self.generate_response(prompt)
        topics = [t.strip() for t in response.split('\n') if t.strip()]
        return topics[:5]
