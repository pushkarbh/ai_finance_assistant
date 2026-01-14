"""
Market data utilities using yFinance.
Provides functions for fetching stock prices, info, and historical data.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import time

import yfinance as yf
import pandas as pd


# Simple in-memory cache
_cache: Dict[str, Dict[str, Any]] = {}
_cache_ttl = 1800  # 30 minutes in seconds


def _get_from_cache(key: str) -> Optional[Any]:
    """Get value from cache if not expired."""
    if key in _cache:
        entry = _cache[key]
        if time.time() - entry['timestamp'] < _cache_ttl:
            return entry['value']
    return None


def _set_cache(key: str, value: Any):
    """Set value in cache."""
    _cache[key] = {
        'value': value,
        'timestamp': time.time()
    }


def get_stock_price(ticker: str) -> Dict[str, Any]:
    """
    Get current stock price and basic info.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dict with price and change info
    """
    cache_key = f"price_{ticker}"
    cached = _get_from_cache(cache_key)
    if cached:
        return cached

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        result = {
            'ticker': ticker,
            'price': info.get('currentPrice') or info.get('regularMarketPrice', 0),
            'previous_close': info.get('previousClose', 0),
            'change': 0,
            'change_pct': 0,
            'volume': info.get('volume', 0),
            'market_cap': info.get('marketCap', 0),
            'name': info.get('shortName', ticker),
            'timestamp': datetime.now().isoformat()
        }

        # Calculate change
        if result['price'] and result['previous_close']:
            result['change'] = result['price'] - result['previous_close']
            result['change_pct'] = (result['change'] / result['previous_close']) * 100

        _set_cache(cache_key, result)
        return result

    except Exception as e:
        return {
            'ticker': ticker,
            'price': 0,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def get_stock_info(ticker: str) -> Dict[str, Any]:
    """
    Get detailed stock information.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dict with company info
    """
    cache_key = f"info_{ticker}"
    cached = _get_from_cache(cache_key)
    if cached:
        return cached

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        result = {
            'ticker': ticker,
            'name': info.get('shortName', ticker),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', None),
            'forward_pe': info.get('forwardPE', None),
            'dividend_yield': info.get('dividendYield', 0),
            'beta': info.get('beta', None),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh', None),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow', None),
            'description': info.get('longBusinessSummary', ''),
            'quoteType': info.get('quoteType', 'EQUITY'),
            'timestamp': datetime.now().isoformat()
        }

        _set_cache(cache_key, result)
        return result

    except Exception as e:
        return {
            'ticker': ticker,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def get_multiple_prices(tickers: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Get prices for multiple tickers.

    Args:
        tickers: List of ticker symbols

    Returns:
        Dict mapping ticker to price info
    """
    results = {}
    for ticker in tickers:
        results[ticker] = get_stock_price(ticker)
    return results


def get_historical_data(
    ticker: str,
    period: str = "1mo",
    interval: str = "1d"
) -> pd.DataFrame:
    """
    Get historical price data.

    Args:
        ticker: Stock ticker symbol
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
        interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo)

    Returns:
        DataFrame with historical prices
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        return hist
    except Exception as e:
        print(f"Error fetching historical data for {ticker}: {e}")
        return pd.DataFrame()


def get_market_summary() -> Dict[str, Any]:
    """
    Get summary of major market indices.

    Returns:
        Dict with major index data
    """
    indices = {
        '^GSPC': 'S&P 500',
        '^DJI': 'Dow Jones',
        '^IXIC': 'NASDAQ',
        '^RUT': 'Russell 2000'
    }

    summary = {}
    for symbol, name in indices.items():
        data = get_stock_price(symbol)
        summary[name] = {
            'symbol': symbol,
            'price': data.get('price', 0),
            'change': data.get('change', 0),
            'change_pct': data.get('change_pct', 0)
        }

    return summary


def get_stock_news(ticker: str, num_news: int = 5) -> List[Dict[str, Any]]:
    """
    Get recent news for a stock.

    Args:
        ticker: Stock ticker symbol
        num_news: Number of news items to return

    Returns:
        List of news items
    """
    try:
        stock = yf.Ticker(ticker)
        news = stock.news[:num_news] if stock.news else []

        return [{
            'title': item.get('title', ''),
            'publisher': item.get('publisher', ''),
            'link': item.get('link', ''),
            'published': datetime.fromtimestamp(item.get('providerPublishTime', 0)).isoformat()
            if item.get('providerPublishTime') else ''
        } for item in news]

    except Exception as e:
        return []


def calculate_returns(
    ticker: str,
    periods: List[str] = ['1mo', '3mo', '6mo', '1y']
) -> Dict[str, float]:
    """
    Calculate returns for various time periods.

    Args:
        ticker: Stock ticker symbol
        periods: List of periods to calculate returns for

    Returns:
        Dict mapping period to return percentage
    """
    returns = {}

    for period in periods:
        try:
            hist = get_historical_data(ticker, period=period)
            if not hist.empty:
                start_price = hist['Close'].iloc[0]
                end_price = hist['Close'].iloc[-1]
                pct_return = ((end_price - start_price) / start_price) * 100
                returns[period] = round(pct_return, 2)
            else:
                returns[period] = None
        except Exception:
            returns[period] = None

    return returns


def get_earnings_info(ticker: str) -> Dict[str, Any]:
    """
    Get earnings information for a stock.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dict with earnings data
    """
    try:
        stock = yf.Ticker(ticker)
        calendar = stock.calendar

        if calendar is None or calendar.empty:
            return {'error': 'No earnings data available'}

        return {
            'ticker': ticker,
            'next_earnings_date': str(calendar.get('Earnings Date', [None])[0]) if 'Earnings Date' in calendar else None,
            'eps_estimate': calendar.get('EPS Estimate', None),
            'revenue_estimate': calendar.get('Revenue Estimate', None)
        }

    except Exception as e:
        return {'ticker': ticker, 'error': str(e)}


def clear_cache():
    """Clear the price cache."""
    global _cache
    _cache = {}
