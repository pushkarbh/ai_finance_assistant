"""
Pytest configuration and shared fixtures for AI Finance Assistant tests.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment variables
os.environ['OPENAI_API_KEY'] = 'test-api-key-for-testing'
os.environ['ALPHA_VANTAGE_API_KEY'] = 'test-alpha-vantage-key'


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    mock_response = MagicMock()
    mock_response.content = "This is a test response from the AI assistant."
    return mock_response


@pytest.fixture
def mock_llm(mock_openai_response):
    """Mock LLM for testing without API calls."""
    with patch('src.core.llm.ChatOpenAI') as mock_chat:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = mock_openai_response
        mock_chat.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_portfolio():
    """Sample portfolio data for testing."""
    return {
        'holdings': [
            {'ticker': 'AAPL', 'shares': 10, 'purchase_price': 150.0},
            {'ticker': 'MSFT', 'shares': 5, 'purchase_price': 280.0},
            {'ticker': 'VTI', 'shares': 20, 'purchase_price': 200.0},
            {'ticker': 'BND', 'shares': 30, 'purchase_price': 75.0},
        ]
    }


@pytest.fixture
def sample_goals():
    """Sample financial goals for testing."""
    return [
        {
            'name': 'Retirement',
            'target_amount': 1000000,
            'current_amount': 50000,
            'target_date': '2050-01-01',
            'monthly_contribution': 1000
        },
        {
            'name': 'House Down Payment',
            'target_amount': 100000,
            'current_amount': 20000,
            'target_date': '2028-01-01',
            'monthly_contribution': 1500
        }
    ]


@pytest.fixture
def sample_agent_state():
    """Sample agent state for testing."""
    from src.core.state import create_initial_state
    return create_initial_state(
        query="What are stocks?",
        session_id="test-session-123"
    )


@pytest.fixture
def sample_documents():
    """Sample documents for RAG testing."""
    from langchain_core.documents import Document
    return [
        Document(
            page_content="Stocks represent ownership in a company. When you buy a stock, you're purchasing a small piece of that company.",
            metadata={"source": "test_doc_1.md", "title": "Understanding Stocks", "category": "investing_basics"}
        ),
        Document(
            page_content="Bonds are fixed-income investments. When you buy a bond, you're lending money to an entity in exchange for interest.",
            metadata={"source": "test_doc_2.md", "title": "Understanding Bonds", "category": "fixed_income"}
        ),
        Document(
            page_content="Diversification means spreading investments across different assets to reduce risk.",
            metadata={"source": "test_doc_3.md", "title": "Diversification", "category": "portfolio_management"}
        ),
    ]


@pytest.fixture
def mock_stock_data():
    """Mock stock price data."""
    return {
        'ticker': 'AAPL',
        'price': 175.50,
        'previous_close': 173.25,
        'change': 2.25,
        'change_pct': 1.30,
        'volume': 50000000,
        'market_cap': 2800000000000,
        'name': 'Apple Inc.'
    }


@pytest.fixture
def mock_market_summary():
    """Mock market summary data."""
    return {
        'S&P 500': {'symbol': '^GSPC', 'price': 4500.0, 'change': 25.0, 'change_pct': 0.56},
        'Dow Jones': {'symbol': '^DJI', 'price': 35000.0, 'change': 150.0, 'change_pct': 0.43},
        'NASDAQ': {'symbol': '^IXIC', 'price': 14000.0, 'change': 75.0, 'change_pct': 0.54},
        'Russell 2000': {'symbol': '^RUT', 'price': 2000.0, 'change': 10.0, 'change_pct': 0.50}
    }


@pytest.fixture
def csv_portfolio_content():
    """Sample CSV content for portfolio upload."""
    return """ticker,shares,purchase_price,purchase_date
AAPL,10,150.00,2023-01-15
MSFT,5,280.00,2023-02-20
VTI,20,200.00,2023-03-10
BND,30,75.00,2023-04-01"""
