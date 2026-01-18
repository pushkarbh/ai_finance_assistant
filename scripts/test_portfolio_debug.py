#!/usr/bin/env python3
"""Test portfolio analysis to debug datetime error."""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agents.portfolio_agent import PortfolioAnalysisAgent

# Test data from sample_portfolio_detailed.csv
portfolio_data = {
    "holdings": [
        {"type": "stock", "ticker": "TSLA", "shares": 100, "purchase_price": 385, "purchase_date": "2021-11-01"},
        {"type": "stock", "ticker": "ARKK", "shares": 200, "purchase_price": 115, "purchase_date": "2021-02-15"},
        {"type": "stock", "ticker": "ZM", "shares": 150, "purchase_price": 350, "purchase_date": "2020-10-20"},
    ]
}

print("Testing portfolio analysis...")
agent = PortfolioAnalysisAgent()

try:
    result = agent.analyze_portfolio(portfolio_data)
    print("✅ Analysis successful!")
    print(f"Total value: ${result.get('total_value', 0):,.2f}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
