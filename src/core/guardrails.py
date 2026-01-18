"""
Guardrails for the AI Finance Assistant.
Implements safety checks, domain validation, and content filtering using Guardrails AI.
"""

from typing import Dict, Optional, Tuple
from guardrails import Guard, Validator, register_validator
from guardrails.errors import ValidationError
from langchain_core.messages import HumanMessage, SystemMessage
from src.core.llm import get_llm


@register_validator(name="finance_topic", data_type="string")
class FinanceTopicValidator(Validator):
    """
    Custom validator to ensure queries are finance-related.
    Uses keyword detection and semantic analysis.
    """
    
    # Finance-related keywords
    FINANCE_KEYWORDS = [
        'invest', 'stock', 'bond', 'portfolio', 'retire', '401k', 'ira',
        'savings', 'market', 'dividend', 'etf', 'mutual fund', 'finance',
        'money', 'dollar', 'economy', 'trading', 'budget', 'loan', 'mortgage',
        'credit', 'debt', 'roth', 'pension', 'asset', 'equity', 'commodit',
        'inflation', 'recession', 'diversif', 'allocation', 'capital gains'
    ]
    
    # Obvious off-topic keywords
    OFF_TOPIC_KEYWORDS = [
        'weather', 'temperature', 'forecast', 'rain', 'snow',
        'recipe', 'cooking', 'food', 'restaurant',
        'movie', 'film', 'tv show', 'netflix',
        'sports', 'game', 'score', 'team',
        'health', 'medical', 'doctor', 'symptom',
        'traffic', 'highway', 'i-90', 'freeway', 'driving',
        'socks', 'clothing', 'shoes', 'fashion'
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.classification = None
    
    def validate(self, value: str, metadata: dict = {}) -> str:
        """Validate that the query is finance-related."""
        query_lower = value.lower()
        
        # Check for obvious off-topic keywords
        for keyword in self.OFF_TOPIC_KEYWORDS:
            if keyword in query_lower:
                # Unless there's finance context
                has_finance = any(fk in query_lower for fk in self.FINANCE_KEYWORDS)
                if not has_finance:
                    self.classification = "OFF_TOPIC"
                    raise ValidationError(
                        f"Query appears to be off-topic (detected: {keyword})"
                    )
        
        # Check for finance keywords
        has_finance_keyword = any(kw in query_lower for kw in self.FINANCE_KEYWORDS)
        
        # For very short queries, be stricter
        if len(value.split()) <= 5 and not has_finance_keyword:
            self.classification = "OFF_TOPIC"
            raise ValidationError(
                "Query does not appear to be finance-related"
            )
        
        return value


@register_validator(name="inappropriate_content", data_type="string")
class InappropriateContentValidator(Validator):
    """
    Validator to detect inappropriate or illegal requests.
    """
    
    INAPPROPRIATE_KEYWORDS = [
        'launder', 'money laundering', 'tax evasion', 'evade tax',
        'insider trading', 'insider information', 'pump and dump',
        'ponzi scheme', 'pyramid scheme', 'scam people',
        'fraud', 'embezzle', 'manipulat', 'illegal'
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.classification = None
    
    def validate(self, value: str, metadata: dict = {}) -> str:
        """Validate that the query doesn't request illegal activities."""
        query_lower = value.lower()
        
        for keyword in self.INAPPROPRIATE_KEYWORDS:
            if keyword in query_lower:
                self.classification = "INAPPROPRIATE"
                raise ValidationError(
                    f"Query contains inappropriate content (detected: {keyword})"
                )
        
        return value


@register_validator(name="scope_validator", data_type="string")
class ScopeValidator(Validator):
    """
    Validator to detect out-of-scope requests requiring professionals.
    """
    
    OUT_OF_SCOPE_KEYWORDS = [
        'file my tax', 'do my tax', 'prepare my tax',
        'draft contract', 'legal agreement', 'write contract',
        'sue', 'lawsuit', 'attorney', 'lawyer',
        'specific tax advice', 'tax loophole'
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.classification = None
    
    def validate(self, value: str, metadata: dict = {}) -> str:
        """Validate that the query is within educational scope."""
        query_lower = value.lower()
        
        for keyword in self.OUT_OF_SCOPE_KEYWORDS:
            if keyword in query_lower:
                self.classification = "OUT_OF_SCOPE"
                raise ValidationError(
                    f"Query requires professional assistance (detected: {keyword})"
                )
        
        return value


@register_validator(name="llm_finance_relevance", data_type="string")
class LLMFinanceRelevanceValidator(Validator):
    """
    LLM-based validator for nuanced finance relevance detection.
    This is used as a final safety layer for ambiguous queries.
    """
    
    RELEVANCE_PROMPT = """You are a strict query classifier for a financial education assistant.

The assistant ONLY helps with FINANCE topics:
- Investing, portfolio management, retirement accounts
- Market data, stock prices, economic indicators  
- Financial planning, budgeting, savings goals
- Financial education and literacy

CRITICAL: Pay attention to MEANING, not just keywords.
- "socks" (clothing) ≠ "stocks" (investments)
- "traffic" (transportation) ≠ "trading" (markets)

Examples:
OFF_TOPIC: "best socks to buy" (clothing), "traffic on I-90" (transportation)
RELEVANT: "best stocks to buy" (investing), "trading strategies" (finance)
INAPPROPRIATE: "evade taxes" (illegal)
OUT_OF_SCOPE: "file my taxes" (needs professional)

Query: "{query}"

Respond with ONLY one word: RELEVANT, OFF_TOPIC, INAPPROPRIATE, or OUT_OF_SCOPE"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.llm = get_llm(temperature=0)
        self.classification = None
    
    def validate(self, value: str, metadata: dict = {}) -> str:
        """Use LLM to validate query relevance for ambiguous cases."""
        prompt = self.RELEVANCE_PROMPT.format(query=value)
        
        messages = [
            SystemMessage(content="You are a query classifier. Respond with only one word."),
            HumanMessage(content=prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            classification = response.content.strip().upper()
            , use_llm_fallback: bool = True):
        """
        Initialize guardrails with custom validators.
        
        Args:
            use_llm_fallback: If True, adds LLM-based validator as final safety layer
                             for ambiguous queries. Uses OpenAI key but only for edge cases.
        """
        # Create validators
        self.finance_validator = FinanceTopicValidator(on_fail="exception")
        self.inappropriate_validator = InappropriateContentValidator(on_fail="exception")
        self.scope_validator = ScopeValidator(on_fail="exception")
        
        validators = [
            self.finance_validator,
            self.inappropriate_validator,
            self.scope_validator
        ]
        
        # Add LLM validator as final safety layer for ambiguous cases
        if use_llm_fallback:
            self.llm_validator = LLMFinanceRelevanceValidator(on_fail="exception")
            validators.append(self.llm_validator)
        else:
            self.llm_validator = None
        
        # Create guard with custom validators
        self.guard = Guard().use_many(*validators    return value
            
        except ValidationError:
            raise  # Re-raise validation errors
        except Exception as e:
            # On error, allow through (fail open)
            print(f"LLM validator error: {e}")
            return value


class QueryGuardrails:
    """
    Validates and filters user queries using Guardrails AI framework.
    Fast, robust validation with custom validators.
    """
    
    REFUSAL_MESSAGES = {
        'OFF_TOPIC': """I appreciate you reaching out! However, I'm specifically designed to help with **financial education and planning**.

I can assist with:
- 📚 Understanding financial concepts (stocks, bonds, retirement, etc.)
- 💼 Analyzing investment portfolios
- 📈 Market data and trends
- 🎯 Financial goal planning
- 💡 General financial literacy

Could I help you with any finance-related questions instead?""",
        
        'INAPPROPRIATE': """I can't assist with that request as it involves activities that may be illegal or unethical.

I'm here to provide **educational financial information** to help you make informed decisions within legal and ethical boundaries.

I'd be happy to help with:
- Learning about legitimate investment strategies
- Understanding financial regulations
- Building long-term wealth through legal means
- Financial planning and education

Is there a different financial topic I can help you explore?""",
        
        'OUT_OF_SCOPE': """I appreciate your question! While this is finance-related, it falls outside my area of expertise.

I focus on:
- 📚 **Financial education** - explaining concepts in beginner-friendly terms
- 💼 **Portfolio analysis** - reviewing investment allocations
- 📈 **Market insights** - data and trends
- 🎯 **Goal planning** - retirement and savings projections

For specialized advice on taxes, legal matters, or detailed compliance issues, I recommend consulting with a qualified:
- Tax professional (CPA or tax attorney)
- Financial advisor (CFP)
- Legal expert in financial law

Is there a general financial education topic I can help explain instead?"""
    }

    def __init__(self):
        """Initialize guardrails with custom validators."""
        # Create validators
        self.finance_validator = FinanceTopicValidator(on_fail="exception")
        self.inappropriate_validator = InappropriateContentValidator(on_fail="exception")
        self.scope_validator = ScopeValidator(on_fail="exception")
        
        # Create guard with custom validators
        self.guard = Guard().use_many(
            self.finance_validator,
            self.inappropriate_validator,
            self.scope_validator
        )
    
    def validate_query(self, query: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate if a query is appropriate and within domain.
        
        Args:
            query: User's query
            
        Returns:
            Tuple of (is_valid, refusal_message, classification)
            - is_valid: True if query should be proce (check in order)
            if hasattr(self.finance_validator, 'classification') and self.finance_validator.classification:
                classification = self.finance_validator.classification
                self.finance_validator.classification = None  # Reset for next use
            elif hasattr(self.inappropriate_validator, 'classification') and self.inappropriate_validator.classification:
                classification = self.inappropriate_validator.classification
                self.inappropriate_validator.classification = None
            elif hasattr(self.scope_validator, 'classification') and self.scope_validator.classification:
                classification = self.scope_validator.classification
                self.scope_validator.classification = None
            elif self.llm_validator and hasattr(self.llm_validator, 'classification') and self.llm_validator.classification:
                classification = self.llm_validator.classification
                self.llmNone, "RELEVANT")
            
        except ValidationError as e:
            # Check which validator failed and get its classification
            classification = "OFF_TOPIC"  # default
            
            # Try to extract from validator instances
            if hasattr(self.finance_validator, 'classification') and self.finance_validator.classification:
                classification = self.finance_validator.classification
                self.finance_validator.classification = None  # Reset for next use
            elif hasattr(self.inappropriate_validator, 'classification') and self.inappropriate_validator.classification:
                classification = self.inappropriate_validator.classification
                self.inappropriate_validator.classification = None
            elif hasattr(self.scope_validator, 'classification') and self.scope_validator.classification:
                classification = self.scope_validator.classification
                self.scope_validator.classification = None
            
            # Get appropriate refusal message
            refusal_message = self.REFUSAL_MESSAGES.get(
                classification,
                self.REFUSAL_MESSAGES['OFF_TOPIC']
            )
            
            return (False, refusal_message, classification)
            
        except Exception as e:
            # On unexpected error, allow through (fail open)
            print(f"Guardrail validation error: {e}")
            return (True, None, "RELEVANT")
    
    def validate_response(self, response: str) -> Tuple[bool, str]:
        """
        Validate that response follows guidelines (optional second layer).
        
        Args:
            response: Generated response
            
        Returns:
            Tuple of (is_valid, validated_response)
        """
        # Check for inappropriate content patterns
        response_lower = response.lower()
        
        # Ensure disclaimer is present for advice-like content
        advice_indicators = ['should', 'recommend', 'suggest', 'advise', 'best to']
        has_advice = any(indicator in response_lower for indicator in advice_indicators)
        has_disclaimer = 'not financial advice' in response_lower or 'educational purposes' in response_lower
        
        if has_advice and not has_disclaimer:
            # Add disclaimer if missing
            disclaimer = "\n\n---\n*This information is for educational purposes only and should not be considered financial advice. Please consult a qualified financial advisor for personalized guidance.*"
            response = response + disclaimer
        
        return (True, response)


# Singleton instance
_guardrails: Optional[QueryGuardrails] = None


def get_guardrails() -> QueryGuardrails:
    """Get the singleton guardrails instance."""
    global _guardrails
    if _guardrails is None:
        _guardrails = QueryGuardrails()
    return _guardrails


def validate_query(query: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Convenience function to validate a query.
    
    Args:
        query: User's query
        
    Returns:
        Tuple of (is_valid, refusal_message, classification)
    """
    guardrails = get_guardrails()
    return guardrails.validate_query(query)
