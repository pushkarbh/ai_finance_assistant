#!/usr/bin/env python3
"""Direct test of yfinance API to see what it actually returns."""

import yfinance as yf
import json

print("=" * 60)
print("TESTING YFINANCE API DIRECTLY")
print("=" * 60)

ticker = "TSLA"
print(f"\nFetching data for {ticker}...")

try:
    stock = yf.Ticker(ticker)
    
    # Check if news attribute exists
    print(f"\nHas 'news' attribute: {hasattr(stock, 'news')}")
    
    # Try to access news
    try:
        news = stock.news
        print(f"Type of stock.news: {type(news)}")
        print(f"Length of stock.news: {len(news) if news else 'None'}")
        
        if news:
            print(f"\n--- First news item (raw) ---")
            print(json.dumps(news[0], indent=2, default=str))
            
            print(f"\n--- All news items (first 3) ---")
            for i, item in enumerate(news[:3]):
                print(f"\nItem {i}:")
                print(f"  Type: {type(item)}")
                print(f"  Keys: {item.keys() if isinstance(item, dict) else 'N/A'}")
                if isinstance(item, dict):
                    for key, value in item.items():
                        print(f"    {key}: {value!r}")
        else:
            print("stock.news is None or empty")
            
    except AttributeError as e:
        print(f"AttributeError accessing stock.news: {e}")
    except Exception as e:
        print(f"Exception accessing stock.news: {type(e).__name__}: {e}")
        
except Exception as e:
    print(f"Exception creating Ticker: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
