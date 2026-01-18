"""Test guardrails with tricky similar-sounding queries."""

from src.core.guardrails import validate_query


def test_tricky_queries():
    """Test queries that sound similar but have different meanings."""
    
    test_cases = [
        # Socks vs Stocks
        ("What are the best socks to buy?", "OFF_TOPIC", "clothing"),
        ("What are the best stocks to buy?", "RELEVANT", "investing"),
        
        # Shoes vs investment
        ("How do I tie my shoes?", "OFF_TOPIC", "clothing/how-to"),
        ("What shoes should I invest in?", "OFF_TOPIC", "shoes as products"),
        ("Should I invest in Nike stock?", "RELEVANT", "Nike as a stock"),
        
        # Restaurants vs budgeting
        ("Best restaurants in NYC", "OFF_TOPIC", "dining"),
        ("How to budget for dining out?", "RELEVANT", "budgeting"),
        
        # Traffic vs Trading
        ("Traffic on highway", "OFF_TOPIC", "transportation"),
        ("Trading on the market", "RELEVANT", "financial markets"),
        
        # Bills vs investments
        ("How do I pay my electric bill?", "OFF_TOPIC", "utilities"),
        ("Should I invest in utility bills?", "RELEVANT", "utility bonds/stocks"),
        
        # General how-to
        ("How to bake bread?", "OFF_TOPIC", "cooking"),
        ("How to balance a portfolio?", "RELEVANT", "portfolio management"),
        
        # Technology products vs tech stocks
        ("Best laptop to buy?", "OFF_TOPIC", "consumer tech"),
        ("Should I buy tech stocks?", "RELEVANT", "tech sector investing"),
    ]
    
    print("=" * 80)
    print("TESTING TRICKY GUARDRAIL QUERIES")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    
    for query, expected, note in test_cases:
        is_valid, message, classification = validate_query(query)
        
        match = classification == expected
        status = "✅" if match else "❌"
        
        if match:
            passed += 1
        else:
            failed += 1
        
        print(f'{status} "{query}"')
        print(f'   Note: {note}')
        print(f'   Expected: {expected}, Got: {classification}')
        
        if not match:
            print(f'   ⚠️  MISMATCH - Guardrail failed to detect properly!')
        
        print()
    
    print("=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed} tests")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = test_tricky_queries()
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed - guardrails need improvement")
        print("\nConsider:")
        print("1. Adding more few-shot examples to the LLM prompt")
        print("2. Using a dedicated classification model (faster + more accurate)")
        print("3. Integrating Guardrails AI framework for production use")
