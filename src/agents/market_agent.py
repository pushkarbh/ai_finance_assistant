"""
Market Analysis Agent for AI Finance Assistant.
Provides real-time market insights and educational context.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from src.agents.base_agent import BaseAgent
from src.core.state import AgentState, update_state_with_agent_output
from src.core.llm import AGENT_SYSTEM_PROMPTS
from src.utils.market_data import (
    get_stock_price,
    get_stock_info,
    get_historical_data,
    get_market_summary,
    get_stock_news,
    calculate_returns
)


class MarketAnalysisAgent(BaseAgent):
    """
    Market Analysis Agent.
    Provides real-time market data and educational insights about
    market trends, individual stocks, and market conditions.
    """

    def __init__(self, system_prompt: Optional[str] = None):
        """
        Initialize the Market Analysis Agent.

        Args:
            system_prompt: Custom system prompt
        """
        super().__init__(
            name="Market Analysis Agent",
            description="Provides real-time market insights and trends",
            system_prompt=system_prompt or AGENT_SYSTEM_PROMPTS["market_analysis"]
        )

    def process(self, state: AgentState) -> AgentState:
        """
        Process market analysis request.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state
        """
        query = state["current_query"]

        # Extract any tickers mentioned in the query
        tickers = self._extract_tickers(query)

        # Get market data
        market_data = {}
        if tickers:
            for ticker in tickers:
                market_data[ticker] = {
                    'price': get_stock_price(ticker),
                    'info': get_stock_info(ticker),
                    'returns': calculate_returns(ticker)
                }
            state["market_data"].update(market_data)

        # Get market summary for context
        market_summary = get_market_summary()

        # Generate response
        response = self.analyze_and_respond(query, market_data, market_summary)

        state = update_state_with_agent_output(state, "market_analysis", {
            "response": response,
            "market_data": market_data,
            "market_summary": market_summary,
            "tickers_analyzed": tickers
        })

        return state

    def _extract_tickers(self, query: str) -> List[str]:
        """
        Extract stock tickers from a query.

        Args:
            query: User query

        Returns:
            List of ticker symbols
        """
        # Common tickers to check for
        common_tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'TSLA', 'NVDA',
            'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'PYPL',
            'VTI', 'VOO', 'SPY', 'QQQ', 'VGT', 'VNQ', 'BND', 'VXUS',
            'SCHD', 'VYM', 'VIG', 'ARKK'
        ]

        found_tickers = []
        query_upper = query.upper()

        for ticker in common_tickers:
            if ticker in query_upper:
                found_tickers.append(ticker)

        # Also look for patterns like $AAPL or (AAPL)
        import re
        patterns = re.findall(r'\$([A-Z]{1,5})|(?:\()([A-Z]{1,5})(?:\))', query_upper)
        for match in patterns:
            ticker = match[0] or match[1]
            if ticker and ticker not in found_tickers:
                found_tickers.append(ticker)

        return found_tickers

    def analyze_and_respond(
        self,
        query: str,
        market_data: Dict[str, Any],
        market_summary: Dict[str, Any]
    ) -> str:
        """
        Analyze market data and generate educational response.

        Args:
            query: User's query
            market_data: Data for specific tickers
            market_summary: Overall market summary

        Returns:
            Educational response
        """
        # Format market summary
        summary_text = self._format_market_summary(market_summary)

        # Format specific ticker data if available
        ticker_text = ""
        if market_data:
            ticker_text = "\n\nSPECIFIC STOCKS MENTIONED:\n"
            for ticker, data in market_data.items():
                price_info = data.get('price', {})
                info = data.get('info', {})
                returns = data.get('returns', {})

                ticker_text += f"""
{ticker} ({info.get('name', ticker)}):
- Current Price: ${price_info.get('price', 0):.2f}
- Change Today: {price_info.get('change_pct', 0):.2f}%
- Sector: {info.get('sector', 'N/A')}
- P/E Ratio: {info.get('pe_ratio', 'N/A')}
- 52-Week Range: ${info.get('fifty_two_week_low', 0):.2f} - ${info.get('fifty_two_week_high', 0):.2f}
- Returns: 1M: {returns.get('1mo', 'N/A')}%, 1Y: {returns.get('1y', 'N/A')}%
"""

        prompt = f"""Based on the current market data, provide an educational response to the user's question.

MARKET OVERVIEW:
{summary_text}
{ticker_text}

USER QUESTION: {query}

Please provide:
1. A clear answer using the current market data
2. Educational context (what this means for investors)
3. Important caveats (past performance, market risks, etc.)

Remember to explain any financial terms and be educational rather than giving specific advice."""

        return self.generate_response(prompt)

    def _format_market_summary(self, summary: Dict[str, Any]) -> str:
        """Format market summary for display."""
        lines = ["Major Indices:"]
        for name, data in summary.items():
            direction = "↑" if data['change'] >= 0 else "↓"
            lines.append(
                f"  {name}: {data['price']:,.2f} {direction} {abs(data['change_pct']):.2f}%"
            )
        return '\n'.join(lines)

    def get_stock_analysis(self, ticker: str) -> str:
        """
        Get detailed analysis for a single stock.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Educational analysis
        """
        price_data = get_stock_price(ticker)
        info = get_stock_info(ticker)
        returns = calculate_returns(ticker)
        news = get_stock_news(ticker, 3)

        prompt = f"""Provide an educational analysis of {ticker} ({info.get('name', ticker)}) for a beginner investor.

CURRENT DATA:
- Price: ${price_data.get('price', 0):.2f}
- Today's Change: {price_data.get('change_pct', 0):.2f}%
- Sector: {info.get('sector', 'N/A')}
- Industry: {info.get('industry', 'N/A')}
- Market Cap: ${info.get('market_cap', 0):,.0f}
- P/E Ratio: {info.get('pe_ratio', 'N/A')}
- Dividend Yield: {(info.get('dividend_yield', 0) or 0) * 100:.2f}%
- Beta: {info.get('beta', 'N/A')}

RETURNS:
- 1 Month: {returns.get('1mo', 'N/A')}%
- 3 Months: {returns.get('3mo', 'N/A')}%
- 6 Months: {returns.get('6mo', 'N/A')}%
- 1 Year: {returns.get('1y', 'N/A')}%

RECENT NEWS HEADLINES:
{chr(10).join([f"- {n['title']}" for n in news]) if news else "No recent news available"}

Please provide:
1. Overview of the company and its business
2. Explanation of the key metrics (what P/E, beta mean)
3. Recent performance context
4. Things to consider (not recommendations)

Be educational and explain concepts for beginners."""

        return self.generate_response(prompt)

    def get_market_overview(self) -> str:
        """
        Get an educational overview of current market conditions.

        Returns:
            Market overview with educational context
        """
        summary = get_market_summary()

        prompt = f"""Provide an educational overview of current market conditions for a beginner investor.

CURRENT MARKET DATA:
{self._format_market_summary(summary)}

Please explain:
1. What each index represents
2. What today's movements might indicate
3. How beginners should interpret market news
4. The importance of long-term perspective

Keep it educational and avoid sensationalism or specific predictions."""

        return self.generate_response(prompt)

    def compare_stocks(self, tickers: List[str]) -> str:
        """
        Compare multiple stocks educationally.

        Args:
            tickers: List of tickers to compare

        Returns:
            Educational comparison
        """
        comparison_data = []
        for ticker in tickers:
            price = get_stock_price(ticker)
            info = get_stock_info(ticker)
            returns = calculate_returns(ticker)
            comparison_data.append({
                'ticker': ticker,
                'name': info.get('name', ticker),
                'price': price.get('price', 0),
                'change_pct': price.get('change_pct', 0),
                'sector': info.get('sector', 'N/A'),
                'pe_ratio': info.get('pe_ratio', 'N/A'),
                'dividend_yield': info.get('dividend_yield', 0),
                'return_1y': returns.get('1y', 'N/A')
            })

        data_text = "\n".join([
            f"{d['ticker']} ({d['name']}): Price ${d['price']:.2f}, "
            f"P/E {d['pe_ratio']}, Sector: {d['sector']}, "
            f"1Y Return: {d['return_1y']}%"
            for d in comparison_data
        ])

        prompt = f"""Compare these stocks educationally for a beginner investor:

{data_text}

Please provide:
1. Brief overview of each company
2. Key similarities and differences
3. What the metrics mean in this comparison
4. Factors to consider when comparing stocks

Do not recommend which to buy - just educate about the comparison process."""

        return self.generate_response(prompt)
