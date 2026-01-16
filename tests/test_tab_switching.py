"""
Test the smart tab switching functionality
NOTE: This is a standalone test of the extraction functions without requiring dependencies
"""
import re
from typing import Optional


def extract_ticker_from_query(query: str) -> Optional[str]:
    """Extract ticker symbol from user query."""
    query_upper = query.upper()
    
    # Look for $ followed by ticker
    dollar_match = re.search(r'\$([A-Z]{1,5})\b', query_upper)
    if dollar_match:
        return dollar_match.group(1)
    
    # Common stock tickers
    common_tickers = {
        'APPLE': 'AAPL',
        'MICROSOFT': 'MSFT',
        'GOOGLE': 'GOOGL',
        'ALPHABET': 'GOOGL',
        'AMAZON': 'AMZN',
        'TESLA': 'TSLA',
        'META': 'META',
        'FACEBOOK': 'META',
        'NVIDIA': 'NVDA',
        'AMD': 'AMD',
        'NETFLIX': 'NFLX',
        'DISNEY': 'DIS',
        'S&P 500': 'SPY',
        'S&P': 'SPY',
        'NASDAQ': 'QQQ',
    }
    
    for name, ticker in common_tickers.items():
        if name in query_upper:
            return ticker
    
    # Words to exclude (common financial terms that aren't tickers)
    excluded_terms = {
        'ETF', 'IRA', 'RSU', 'ESG', 'IPO', 'CEO', 'CFO', 'SEC',
        'STOCK', 'BOND', 'FUND', 'WHAT', 'HOW', 'WHY', 'WHO', 'WHEN',
        'IS', 'ARE', 'CAN', 'DOES', 'THE', 'AND', 'OR', 'FOR', 'WITH'
    }
    
    # Look for standalone tickers
    words = query_upper.split()
    for word in words:
        clean_word = re.sub(r'[^A-Z]', '', word)
        if len(clean_word) >= 1 and len(clean_word) <= 5 and clean_word.isalpha():
            # Skip excluded terms
            if clean_word in excluded_terms:
                continue
            if clean_word in query:
                return clean_word
    
    return None


def extract_dollar_amount(query: str) -> Optional[float]:
    """Extract dollar amount from query."""
    patterns = [
        r'\$([0-9,]+\.?[0-9]*)\s*(?:million|M)',
        r'\$([0-9,]+\.?[0-9]*)\s*(?:thousand|K)',
        r'\$([0-9,]+\.?[0-9]*)',
        r'([0-9,]+\.?[0-9]*)\s*(?:million|M)',
        r'([0-9,]+\.?[0-9]*)\s*(?:thousand|K)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                amount = float(amount_str)
                if re.search(r'million|M', match.group(0), re.IGNORECASE):
                    amount *= 1_000_000
                elif re.search(r'thousand|K', match.group(0), re.IGNORECASE):
                    amount *= 1_000
                return amount
            except ValueError:
                continue
    
    return None


def test_ticker_extraction():
    """Test ticker extraction from various query formats"""
    test_cases = [
        ("How is Apple stock doing?", "AAPL"),
        ("What's the price of $MSFT?", "MSFT"),
        ("Tell me about TSLA", "TSLA"),
        ("How's Microsoft doing today?", "MSFT"),
        ("What about Google?", "GOOGL"),
        ("S&P 500 performance", "SPY"),
        ("Is AAPL a good buy?", "AAPL"),
        ("Amazon stock analysis", "AMZN"),
        ("What is an ETF?", None),  # No ticker
    ]
    
    print("Testing Ticker Extraction:")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for query, expected in test_cases:
        result = extract_ticker_from_query(query)
        status = "✓" if result == expected else "✗"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"{status} Query: '{query}'")
        print(f"  Expected: {expected}, Got: {result}")
        print()
    
    return passed, failed


def test_amount_extraction():
    """Test dollar amount extraction from queries"""
    test_cases = [
        ("I want to save $100,000 for retirement", 100000),
        ("How can I save $1M?", 1000000),
        ("Need $500K for a house", 500000),
        ("Goal is $1.5 million", 1500000),
        ("Save 100K", 100000),
        ("Retire with 2M", 2000000),
        ("What is an IRA?", None),  # No amount
    ]
    
    print("\nTesting Amount Extraction:")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for query, expected in test_cases:
        result = extract_dollar_amount(query)
        status = "✓" if result == expected else "✗"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"{status} Query: '{query}'")
        print(f"  Expected: {expected}, Got: {result}")
        print()
    
    return passed, failed


def test_agent_mapping():
    """Test agent to tab mapping"""
    print("\nAgent to Tab Mapping:")
    print("=" * 60)
    
    AGENT_TO_TAB = {
        'market_analysis': 2,
        'portfolio_analysis': 1,
        'goal_planning': 3,
        'news_synthesizer': 2,
        'finance_qa': 0,
    }
    
    tab_names = ["Chat", "Portfolio", "Market", "Goals"]
    
    for agent, tab_idx in AGENT_TO_TAB.items():
        tab_name = tab_names[tab_idx] if tab_idx < len(tab_names) else "Unknown"
        print(f"  {agent:20s} → Tab {tab_idx}: {tab_name}")
    
    print()


if __name__ == "__main__":
    ticker_passed, ticker_failed = test_ticker_extraction()
    amount_passed, amount_failed = test_amount_extraction()
    test_agent_mapping()
    
    total_passed = ticker_passed + amount_passed
    total_failed = ticker_failed + amount_failed
    
    print("=" * 60)
    print(f"Tests complete!")
    print(f"  Passed: {total_passed}")
    print(f"  Failed: {total_failed}")
    print("=" * 60)
    
    if total_failed == 0:
        print("✓ All tests passed!")
    else:
        print(f"✗ {total_failed} tests failed")
        exit(1)
