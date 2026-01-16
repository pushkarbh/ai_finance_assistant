"""
Query analyzer for detecting intent and extracting parameters.
Used for smart tab routing in the UI.
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class QueryIntent(str, Enum):
    """Types of query intents for tab routing."""
    CHAT = "chat"  # General education/Q&A - stay on chat tab
    MARKET = "market"  # Stock lookup, price check - go to market tab
    PORTFOLIO = "portfolio"  # Portfolio analysis - go to portfolio tab
    GOALS = "goals"  # Goal planning - go to goals tab


@dataclass
class QueryAnalysis:
    """Result of analyzing a query."""
    intent: QueryIntent
    confidence: float
    extracted_params: Dict[str, Any]
    should_switch_tab: bool
    target_tab: Optional[str] = None


class QueryAnalyzer:
    """
    Analyzes user queries to determine intent and extract parameters.
    Used for smart tab routing in the Streamlit UI.
    """

    # Common stock ticker pattern (1-5 uppercase letters)
    TICKER_PATTERN = r'\b([A-Z]{1,5})\b'

    # Known major tickers to avoid false positives
    KNOWN_TICKERS = {
        'AAPL', 'GOOGL', 'GOOG', 'MSFT', 'AMZN', 'META', 'TSLA', 'NVDA',
        'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'PYPL', 'NFLX',
        'ADBE', 'CRM', 'INTC', 'CSCO', 'PFE', 'ABT', 'TMO', 'VZ', 'T',
        'SPY', 'QQQ', 'VTI', 'VOO', 'IWM', 'VEA', 'VWO', 'BND', 'AGG',
        'VNQ', 'GLD', 'SLV', 'XLF', 'XLE', 'XLK', 'XLV', 'XLI', 'XLP',
        'VXUS', 'SCHD', 'VIG', 'VYM', 'ARKK', 'ARKG',
        'IBM', 'ORCL', 'AMD', 'MU', 'QCOM', 'TXN', 'AVGO', 'NOW',
        'BA', 'CAT', 'MMM', 'GE', 'HON', 'LMT', 'RTX', 'UPS', 'FDX',
        'WMT', 'COST', 'TGT', 'LOW', 'NKE', 'SBUX', 'MCD',
        'KO', 'PEP', 'PM', 'MO', 'CL', 'EL', 'MDLZ',
        'BAC', 'WFC', 'C', 'GS', 'MS', 'AXP', 'BLK', 'SCHW',
        'CVX', 'XOM', 'COP', 'SLB', 'EOG', 'PSX', 'VLO',
        'LLY', 'MRK', 'ABBV', 'BMY', 'GILD', 'AMGN', 'REGN', 'VRTX',
        'NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'SRE',
        'AMT', 'PLD', 'CCI', 'EQIX', 'SPG', 'PSA', 'O', 'WELL'
    }

    # Words that should NOT be treated as tickers
    EXCLUDED_WORDS = {
        'I', 'A', 'AN', 'THE', 'AND', 'OR', 'BUT', 'FOR', 'AT', 'BY',
        'TO', 'IN', 'ON', 'IS', 'IT', 'IF', 'OF', 'AS', 'SO', 'UP',
        'DO', 'GO', 'BE', 'WE', 'HE', 'ME', 'MY', 'NO', 'US', 'AM',
        'ETF', 'IRA', 'RSU', 'CEO', 'CFO', 'IPO', 'SEC', 'GDP', 'APR',
        'APY', 'ROI', 'YTD', 'QTD', 'MTD', 'PE', 'EPS', 'P', 'E',
        'USD', 'EUR', 'GBP', 'CAD', 'AUD', 'OK', 'VS', 'FAQ', 'AI'
    }

    # Market-related keywords
    MARKET_KEYWORDS = [
        'price', 'trading', 'stock price', 'quote', 'lookup', 'look up',
        'check', 'how is', "how's", 'what is', "what's", 'show me',
        'current price', 'market cap', 'pe ratio', 'p/e', 'dividend yield',
        'today', 'right now', 'currently', 'trading at'
    ]

    # Portfolio-related keywords
    PORTFOLIO_KEYWORDS = [
        'portfolio', 'holdings', 'analyze', 'analysis', 'my stocks',
        'my investments', 'diversification', 'allocation', 'rebalance',
        'sector', 'exposure', 'concentrated', 'weighted'
    ]

    # Goal-related keywords
    GOAL_KEYWORDS = [
        'goal', 'plan', 'save', 'saving', 'retirement', 'retire',
        'house', 'down payment', 'college', 'education', 'emergency fund',
        'how much', 'need to save', 'years', 'monthly', 'target',
        'reach', 'achieve', 'accumulate', 'grow to'
    ]

    # Goal types mapping
    GOAL_TYPES = {
        'retirement': 'Retirement',
        'retire': 'Retirement',
        'house': 'House Down Payment',
        'home': 'House Down Payment',
        'down payment': 'House Down Payment',
        'college': 'Education',
        'education': 'Education',
        'university': 'Education',
        'school': 'Education',
        'emergency': 'Emergency Fund',
        'rainy day': 'Emergency Fund'
    }

    def analyze(self, query: str) -> QueryAnalysis:
        """
        Analyze a query to determine intent and extract parameters.

        Args:
            query: User's input query

        Returns:
            QueryAnalysis with intent, confidence, and extracted params
        """
        query_lower = query.lower()

        # Check for market intent (stock lookups)
        market_result = self._check_market_intent(query, query_lower)
        if market_result.should_switch_tab:
            return market_result

        # Check for goals intent
        goals_result = self._check_goals_intent(query, query_lower)
        if goals_result.should_switch_tab:
            return goals_result

        # Check for portfolio intent
        portfolio_result = self._check_portfolio_intent(query, query_lower)
        if portfolio_result.should_switch_tab:
            return portfolio_result

        # Default to chat (general Q&A)
        return QueryAnalysis(
            intent=QueryIntent.CHAT,
            confidence=0.5,
            extracted_params={},
            should_switch_tab=False,
            target_tab=None
        )

    def _check_market_intent(self, query: str, query_lower: str) -> QueryAnalysis:
        """Check if query is asking about market data for a specific stock."""
        # Look for market keywords
        has_market_keyword = any(kw in query_lower for kw in self.MARKET_KEYWORDS)

        # Extract potential tickers
        tickers = self._extract_tickers(query)

        if tickers and has_market_keyword:
            return QueryAnalysis(
                intent=QueryIntent.MARKET,
                confidence=0.9,
                extracted_params={'tickers': tickers, 'primary_ticker': tickers[0]},
                should_switch_tab=True,
                target_tab='market'
            )

        # Even without explicit keywords, if it looks like "AAPL?" or "What about MSFT"
        if tickers and len(query.split()) <= 5:
            return QueryAnalysis(
                intent=QueryIntent.MARKET,
                confidence=0.7,
                extracted_params={'tickers': tickers, 'primary_ticker': tickers[0]},
                should_switch_tab=True,
                target_tab='market'
            )

        return QueryAnalysis(
            intent=QueryIntent.CHAT,
            confidence=0.3,
            extracted_params={'tickers': tickers} if tickers else {},
            should_switch_tab=False
        )

    def _check_goals_intent(self, query: str, query_lower: str) -> QueryAnalysis:
        """Check if query is about financial goal planning."""
        has_goal_keyword = any(kw in query_lower for kw in self.GOAL_KEYWORDS)

        if not has_goal_keyword:
            return QueryAnalysis(
                intent=QueryIntent.CHAT,
                confidence=0.3,
                extracted_params={},
                should_switch_tab=False
            )

        # Extract goal parameters
        params = {}

        # Detect goal type
        for key, goal_type in self.GOAL_TYPES.items():
            if key in query_lower:
                params['goal_type'] = goal_type
                break

        # Extract dollar amounts
        amounts = re.findall(r'\$?([\d,]+(?:\.\d{2})?)\s*(?:k|K|thousand|million|M)?', query)
        if amounts:
            # Convert to float, handling 'k' suffix
            parsed_amounts = []
            for amt in amounts:
                amt_clean = amt.replace(',', '')
                try:
                    value = float(amt_clean)
                    # Check if followed by k/K/thousand
                    if re.search(rf'{re.escape(amt)}\s*[kK]|{re.escape(amt)}\s*thousand', query):
                        value *= 1000
                    elif re.search(rf'{re.escape(amt)}\s*[mM]|{re.escape(amt)}\s*million', query):
                        value *= 1000000
                    parsed_amounts.append(value)
                except ValueError:
                    continue

            if parsed_amounts:
                params['target_amount'] = max(parsed_amounts)  # Assume largest is target

        # Extract years
        years_match = re.search(r'(\d+)\s*(?:years?|yrs?)', query_lower)
        if years_match:
            params['years'] = int(years_match.group(1))

        # Extract monthly contribution
        monthly_match = re.search(r'\$?([\d,]+)\s*(?:per month|monthly|/month|a month)', query_lower)
        if monthly_match:
            params['monthly_contribution'] = float(monthly_match.group(1).replace(',', ''))

        return QueryAnalysis(
            intent=QueryIntent.GOALS,
            confidence=0.85,
            extracted_params=params,
            should_switch_tab=True,
            target_tab='goals'
        )

    def _check_portfolio_intent(self, query: str, query_lower: str) -> QueryAnalysis:
        """Check if query is about portfolio analysis."""
        has_portfolio_keyword = any(kw in query_lower for kw in self.PORTFOLIO_KEYWORDS)

        if not has_portfolio_keyword:
            return QueryAnalysis(
                intent=QueryIntent.CHAT,
                confidence=0.3,
                extracted_params={},
                should_switch_tab=False
            )

        # Extract tickers if mentioned
        tickers = self._extract_tickers(query)

        params = {}
        if tickers:
            params['tickers'] = tickers

        # Check for specific analysis requests
        if 'diversif' in query_lower:
            params['analysis_type'] = 'diversification'
        elif 'allocation' in query_lower:
            params['analysis_type'] = 'allocation'
        elif 'sector' in query_lower:
            params['analysis_type'] = 'sector'

        return QueryAnalysis(
            intent=QueryIntent.PORTFOLIO,
            confidence=0.8,
            extracted_params=params,
            should_switch_tab=True,
            target_tab='portfolio'
        )

    def _extract_tickers(self, query: str) -> List[str]:
        """Extract stock tickers from query."""
        # Find all potential tickers (uppercase words 1-5 chars)
        potential_tickers = re.findall(self.TICKER_PATTERN, query)

        # Filter to known tickers or validate
        tickers = []
        for ticker in potential_tickers:
            if ticker in self.EXCLUDED_WORDS:
                continue
            if ticker in self.KNOWN_TICKERS:
                tickers.append(ticker)
            # Could also validate against an API, but for now just use known list

        return list(dict.fromkeys(tickers))  # Remove duplicates, preserve order


# Singleton instance
_analyzer: Optional[QueryAnalyzer] = None


def get_query_analyzer() -> QueryAnalyzer:
    """Get the singleton query analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = QueryAnalyzer()
    return _analyzer


def analyze_query(query: str) -> QueryAnalysis:
    """Convenience function to analyze a query."""
    return get_query_analyzer().analyze(query)
