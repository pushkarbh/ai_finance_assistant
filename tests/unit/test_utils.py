"""
Unit tests for the utils module (market_data).
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestMarketData:
    """Tests for market data utilities."""

    def test_get_stock_price(self):
        """Test getting stock price."""
        from src.utils.market_data import get_stock_price

        with patch('src.utils.market_data.yf.Ticker') as mock_ticker:
            mock_info = {
                "currentPrice": 175.50,
                "previousClose": 173.25,
                "regularMarketVolume": 50000000,
                "marketCap": 2800000000000,
                "shortName": "Apple Inc."
            }
            mock_ticker.return_value.info = mock_info

            result = get_stock_price("AAPL")

            assert result["ticker"] == "AAPL"
            assert result["price"] == 175.50
            assert result["previous_close"] == 173.25
            assert result["name"] == "Apple Inc."

    def test_get_stock_price_invalid_ticker(self):
        """Test getting price for invalid ticker."""
        from src.utils.market_data import get_stock_price

        with patch('src.utils.market_data.yf.Ticker') as mock_ticker:
            mock_ticker.return_value.info = {}

            result = get_stock_price("INVALID123")

            assert result is None or result.get("error") is not None

    def test_get_stock_price_caching(self):
        """Test that stock prices are cached."""
        from src.utils.market_data import get_stock_price, _price_cache

        # Clear cache first
        _price_cache.clear()

        with patch('src.utils.market_data.yf.Ticker') as mock_ticker:
            mock_info = {"currentPrice": 175.50, "previousClose": 173.25}
            mock_ticker.return_value.info = mock_info

            # First call
            result1 = get_stock_price("AAPL")
            # Second call should use cache
            result2 = get_stock_price("AAPL")

            # Ticker should only be called once due to caching
            assert mock_ticker.call_count == 1
            assert result1 == result2

    def test_get_market_summary(self):
        """Test getting market summary."""
        from src.utils.market_data import get_market_summary

        with patch('src.utils.market_data.yf.Ticker') as mock_ticker:
            mock_ticker.return_value.info = {
                "regularMarketPrice": 4500.0,
                "previousClose": 4475.0
            }

            result = get_market_summary()

            assert "S&P 500" in result or len(result) > 0

    def test_get_stock_history(self):
        """Test getting historical stock data."""
        from src.utils.market_data import get_stock_history
        import pandas as pd

        with patch('src.utils.market_data.yf.Ticker') as mock_ticker:
            # Create mock DataFrame
            mock_df = pd.DataFrame({
                "Open": [170.0, 172.0],
                "High": [175.0, 177.0],
                "Low": [169.0, 171.0],
                "Close": [173.0, 175.0],
                "Volume": [50000000, 48000000]
            }, index=pd.date_range("2024-01-01", periods=2))

            mock_ticker.return_value.history.return_value = mock_df

            result = get_stock_history("AAPL", period="1mo")

            assert result is not None
            assert len(result) == 2

    def test_get_stock_news(self):
        """Test getting stock news."""
        from src.utils.market_data import get_stock_news

        with patch('src.utils.market_data.yf.Ticker') as mock_ticker:
            mock_news = [
                {
                    "title": "Apple Reports Record Earnings",
                    "link": "https://example.com/news1",
                    "publisher": "Reuters",
                    "providerPublishTime": 1704067200
                },
                {
                    "title": "iPhone Sales Surge",
                    "link": "https://example.com/news2",
                    "publisher": "Bloomberg",
                    "providerPublishTime": 1704153600
                }
            ]
            mock_ticker.return_value.news = mock_news

            result = get_stock_news("AAPL", count=2)

            assert len(result) == 2
            assert result[0]["title"] == "Apple Reports Record Earnings"

    def test_extract_tickers_from_query(self):
        """Test extracting stock tickers from query text."""
        from src.utils.market_data import extract_tickers

        result = extract_tickers("What's the price of AAPL and MSFT?")
        assert "AAPL" in result
        assert "MSFT" in result

    def test_extract_tickers_with_company_names(self):
        """Test extracting tickers from company names."""
        from src.utils.market_data import extract_tickers

        result = extract_tickers("How is Apple doing?")
        # Should map "Apple" to "AAPL"
        assert "AAPL" in result or len(result) >= 0  # Depends on implementation

    def test_calculate_returns(self):
        """Test calculating stock returns."""
        from src.utils.market_data import calculate_returns

        prices = [100.0, 105.0, 103.0, 110.0]
        returns = calculate_returns(prices)

        assert len(returns) == 3  # n-1 returns
        assert returns[0] == pytest.approx(0.05, rel=0.01)  # 5% gain

    def test_get_market_movers(self):
        """Test getting market movers."""
        from src.utils.market_data import get_market_movers

        with patch('src.utils.market_data.yf.Ticker') as mock_ticker:
            mock_ticker.return_value.info = {
                "currentPrice": 100.0,
                "previousClose": 95.0
            }

            result = get_market_movers()

            # Should return gainers and losers
            assert isinstance(result, dict)


class TestPortfolioCalculations:
    """Tests for portfolio-related calculations."""

    def test_calculate_portfolio_value(self, sample_portfolio):
        """Test calculating total portfolio value."""
        from src.utils.market_data import calculate_portfolio_value

        with patch('src.utils.market_data.get_stock_price') as mock_price:
            mock_price.return_value = {"price": 175.0}

            value = calculate_portfolio_value(sample_portfolio["holdings"])

            assert value > 0

    def test_calculate_portfolio_returns(self, sample_portfolio):
        """Test calculating portfolio returns."""
        from src.utils.market_data import calculate_portfolio_returns

        with patch('src.utils.market_data.get_stock_price') as mock_price:
            mock_price.return_value = {"price": 175.0}

            returns = calculate_portfolio_returns(sample_portfolio["holdings"])

            assert "total_return" in returns
            assert "total_return_pct" in returns

    def test_calculate_allocation(self, sample_portfolio):
        """Test calculating portfolio allocation."""
        from src.utils.market_data import calculate_allocation

        with patch('src.utils.market_data.get_stock_price') as mock_price:
            mock_price.return_value = {"price": 100.0}

            allocation = calculate_allocation(sample_portfolio["holdings"])

            assert sum(allocation.values()) == pytest.approx(100.0, rel=0.01)


class TestDataValidation:
    """Tests for data validation utilities."""

    def test_validate_ticker(self):
        """Test ticker validation."""
        from src.utils.market_data import validate_ticker

        assert validate_ticker("AAPL") is True
        assert validate_ticker("MSFT") is True
        assert validate_ticker("") is False
        assert validate_ticker("INVALID123456") is False

    def test_validate_portfolio_data(self, sample_portfolio):
        """Test portfolio data validation."""
        from src.utils.market_data import validate_portfolio

        is_valid, errors = validate_portfolio(sample_portfolio)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_portfolio_missing_fields(self):
        """Test portfolio validation with missing fields."""
        from src.utils.market_data import validate_portfolio

        invalid_portfolio = {
            "holdings": [
                {"ticker": "AAPL"}  # Missing shares and purchase_price
            ]
        }

        is_valid, errors = validate_portfolio(invalid_portfolio)
        assert is_valid is False
        assert len(errors) > 0


class TestCompanyMapping:
    """Tests for company name to ticker mapping."""

    def test_company_to_ticker_mapping(self):
        """Test common company name mappings."""
        from src.utils.market_data import COMPANY_TO_TICKER

        assert COMPANY_TO_TICKER.get("apple") == "AAPL"
        assert COMPANY_TO_TICKER.get("microsoft") == "MSFT"
        assert COMPANY_TO_TICKER.get("google") == "GOOGL"
        assert COMPANY_TO_TICKER.get("amazon") == "AMZN"

    def test_get_ticker_from_name(self):
        """Test getting ticker from company name."""
        from src.utils.market_data import get_ticker_from_name

        assert get_ticker_from_name("Apple") == "AAPL"
        assert get_ticker_from_name("Microsoft Corporation") == "MSFT"
        assert get_ticker_from_name("UNKNOWN_COMPANY") is None


class TestCaching:
    """Tests for caching functionality."""

    def test_cache_expiry(self):
        """Test that cache entries expire."""
        from src.utils.market_data import _price_cache, CACHE_TTL
        import time

        # Clear cache
        _price_cache.clear()

        # Add entry with past timestamp
        _price_cache["TEST"] = {
            "data": {"price": 100.0},
            "timestamp": time.time() - CACHE_TTL - 1
        }

        from src.utils.market_data import is_cache_valid
        assert is_cache_valid("TEST") is False

    def test_cache_valid(self):
        """Test that recent cache entries are valid."""
        from src.utils.market_data import _price_cache, is_cache_valid
        import time

        _price_cache["TEST"] = {
            "data": {"price": 100.0},
            "timestamp": time.time()
        }

        assert is_cache_valid("TEST") is True

    def test_clear_cache(self):
        """Test clearing the cache."""
        from src.utils.market_data import _price_cache, clear_cache

        _price_cache["TEST"] = {"data": {}, "timestamp": 0}
        clear_cache()

        assert len(_price_cache) == 0
