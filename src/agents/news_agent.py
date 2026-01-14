"""
News Synthesizer Agent for AI Finance Assistant.
Summarizes and contextualizes financial news for beginners.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from src.agents.base_agent import BaseAgent
from src.core.state import AgentState, update_state_with_agent_output
from src.core.llm import AGENT_SYSTEM_PROMPTS
from src.utils.market_data import get_stock_news, get_market_summary, get_stock_price


class NewsSynthesizerAgent(BaseAgent):
    """
    News Synthesizer Agent.
    Retrieves, summarizes, and provides educational context for
    financial news to help beginners understand market events.
    """

    def __init__(self, system_prompt: Optional[str] = None):
        """
        Initialize the News Synthesizer Agent.

        Args:
            system_prompt: Custom system prompt
        """
        super().__init__(
            name="News Synthesizer Agent",
            description="Summarizes and contextualizes financial news",
            system_prompt=system_prompt or AGENT_SYSTEM_PROMPTS["news_synthesizer"]
        )

    def process(self, state: AgentState) -> AgentState:
        """
        Process news synthesis request.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state
        """
        query = state["current_query"]

        # Extract any specific tickers mentioned
        tickers = self._extract_tickers(query)

        # Gather news
        news_data = {}
        if tickers:
            for ticker in tickers:
                news_data[ticker] = get_stock_news(ticker, num_news=5)
        else:
            # Get news for major indices/popular stocks
            default_tickers = ['SPY', 'AAPL', 'MSFT', 'GOOGL']
            for ticker in default_tickers:
                news_data[ticker] = get_stock_news(ticker, num_news=3)

        # Get market context
        market_summary = get_market_summary()

        # Generate synthesis
        response = self.synthesize_news(query, news_data, market_summary)

        state = update_state_with_agent_output(state, "news_synthesizer", {
            "response": response,
            "news_data": news_data,
            "tickers_covered": list(news_data.keys())
        })

        return state

    def _extract_tickers(self, query: str) -> List[str]:
        """Extract stock tickers from query."""
        common_tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'TSLA', 'NVDA',
            'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'PYPL',
            'SPY', 'QQQ', 'VTI', 'VOO'
        ]

        found = []
        query_upper = query.upper()
        for ticker in common_tickers:
            if ticker in query_upper:
                found.append(ticker)

        return found

    def synthesize_news(
        self,
        query: str,
        news_data: Dict[str, List[Dict]],
        market_summary: Dict[str, Any]
    ) -> str:
        """
        Synthesize news into educational summary.

        Args:
            query: User's query
            news_data: News articles by ticker
            market_summary: Current market summary

        Returns:
            Educational news synthesis
        """
        # Format news headlines
        news_text = self._format_news(news_data)

        # Format market summary
        market_text = self._format_market_summary(market_summary)

        prompt = f"""Synthesize the following financial news for a beginner investor.

CURRENT MARKET CONDITIONS:
{market_text}

RECENT NEWS:
{news_text}

USER QUESTION: {query}

Please provide:
1. Summary of the key news stories
2. What this news means for investors (educational context)
3. How it relates to broader market conditions
4. Important caveats (avoid speculation, note uncertainties)

Keep the tone balanced and educational. Explain any financial terms used.
Avoid sensationalism and specific predictions about stock movements."""

        return self.generate_response(prompt)

    def _format_news(self, news_data: Dict[str, List[Dict]]) -> str:
        """Format news data for the prompt."""
        lines = []
        for ticker, articles in news_data.items():
            if articles:
                lines.append(f"\n{ticker} News:")
                for article in articles:
                    lines.append(f"  - {article.get('title', 'No title')}")
                    lines.append(f"    Source: {article.get('publisher', 'Unknown')}")
                    lines.append(f"    Date: {article.get('published', 'Unknown')}")

        return '\n'.join(lines) if lines else "No recent news available"

    def _format_market_summary(self, summary: Dict[str, Any]) -> str:
        """Format market summary for display."""
        lines = []
        for name, data in summary.items():
            direction = "↑" if data['change'] >= 0 else "↓"
            lines.append(
                f"{name}: {data['price']:,.2f} {direction} {abs(data['change_pct']):.2f}%"
            )
        return '\n'.join(lines)

    def get_daily_briefing(self) -> str:
        """
        Generate a daily market briefing for beginners.

        Returns:
            Educational daily briefing
        """
        # Get market data
        market_summary = get_market_summary()

        # Get news for major indices
        spy_news = get_stock_news('SPY', 3)
        qqq_news = get_stock_news('QQQ', 3)

        all_news = {'S&P 500 (SPY)': spy_news, 'NASDAQ (QQQ)': qqq_news}
        news_text = self._format_news(all_news)
        market_text = self._format_market_summary(market_summary)

        prompt = f"""Create an educational daily market briefing for beginner investors.

TODAY'S MARKET:
{market_text}

TODAY'S NEWS:
{news_text}

Please provide a friendly, educational briefing that includes:
1. Overview of how markets are doing today
2. Key news stories and what they mean
3. Educational context (why this matters to long-term investors)
4. Reminder about staying focused on long-term goals

Keep it concise, balanced, and beginner-friendly.
Avoid specific predictions or recommendations."""

        return self.generate_response(prompt)

    def explain_market_event(self, event_description: str) -> str:
        """
        Explain a specific market event to beginners.

        Args:
            event_description: Description of the market event

        Returns:
            Educational explanation
        """
        market_summary = get_market_summary()
        market_text = self._format_market_summary(market_summary)

        prompt = f"""Explain this market event to a beginner investor:

EVENT: {event_description}

CURRENT MARKET CONDITIONS:
{market_text}

Please provide:
1. What happened in simple terms
2. Why it happened (if known)
3. What it might mean for different types of investors
4. Historical context (have similar events happened before?)
5. How beginners should think about this

Be balanced and educational. Avoid panic-inducing language.
Emphasize that short-term events are normal in markets."""

        return self.generate_response(prompt)

    def get_ticker_news_summary(self, ticker: str) -> str:
        """
        Get a news summary for a specific ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Educational news summary
        """
        news = get_stock_news(ticker, num_news=5)
        price_data = get_stock_price(ticker)

        if not news:
            return f"No recent news found for {ticker}."

        news_text = "\n".join([
            f"- {article['title']} ({article['publisher']})"
            for article in news
        ])

        prompt = f"""Summarize the recent news for {ticker} for a beginner investor.

CURRENT PRICE: ${price_data.get('price', 0):.2f} ({price_data.get('change_pct', 0):.2f}% today)

RECENT NEWS:
{news_text}

Please provide:
1. Summary of the main news themes
2. What this might mean for the company
3. Context for how to interpret company-specific news
4. Reminder about the difference between news and investment decisions

Keep it educational and balanced."""

        return self.generate_response(prompt)

    def compare_news_sentiment(self, tickers: List[str]) -> str:
        """
        Compare news sentiment across multiple tickers.

        Args:
            tickers: List of tickers to compare

        Returns:
            Comparative news analysis
        """
        news_data = {}
        for ticker in tickers:
            news_data[ticker] = get_stock_news(ticker, 3)
            news_data[ticker + '_price'] = get_stock_price(ticker)

        news_text = self._format_news({
            t: news_data[t] for t in tickers if t in news_data
        })

        price_text = "\n".join([
            f"{t}: ${news_data.get(t + '_price', {}).get('price', 0):.2f} "
            f"({news_data.get(t + '_price', {}).get('change_pct', 0):.2f}%)"
            for t in tickers
        ])

        prompt = f"""Compare the recent news coverage for these stocks educationally:

CURRENT PRICES:
{price_text}

NEWS COVERAGE:
{news_text}

Please provide:
1. Summary of news themes for each stock
2. Any patterns or differences in coverage
3. Educational note about how news affects stocks differently
4. Caution about making decisions based on news sentiment

Be balanced and educational."""

        return self.generate_response(prompt)
