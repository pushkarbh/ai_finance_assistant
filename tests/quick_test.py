from src.core.guardrails import get_guardrails

g = get_guardrails()

# Test 1: Off-topic
result1 = g.validate_query("What are the best socks to buy?")
print(f"Test 1 - Socks: {result1}")

# Test 2: Finance
result2 = g.validate_query("What are the best stocks to buy?")
print(f"Test 2 - Stocks: {result2}")

# Test 3: Weather
result3 = g.validate_query("What's the weather in Boston?")
print(f"Test 3 - Weather: {result3}")

# Test 4: Inappropriate
result4 = g.validate_query("How to evade taxes?")
print(f"Test 4 - Tax evasion: {result4}")

print("\nDone!")
