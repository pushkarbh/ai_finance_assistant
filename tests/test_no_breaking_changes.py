"""
Integration test to ensure caching didn't break existing functionality.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.workflow.graph import process_query

def test_basic_queries():
    """Test that basic queries still work."""
    print("\n=== Testing Basic Functionality ===\n")
    
    test_cases = [
        ("What is a stock?", None, None),
        ("Explain 401k", None, None),
        ("How does compound interest work?", None, None),
    ]
    
    for query, portfolio, goals in test_cases:
        print(f"Query: '{query}'")
        try:
            result = process_query(query, portfolio=portfolio, goals=goals)
            
            # Check result structure
            assert 'response' in result, "Missing 'response' key"
            assert 'agents_used' in result, "Missing 'agents_used' key"
            assert 'sources' in result, "Missing 'sources' key"
            
            # Check response is not empty
            assert len(result['response']) > 0, "Empty response"
            
            print(f"  ✅ Response: {len(result['response'])} chars")
            print(f"  ✅ Agents: {result.get('agents_used', [])}")
            print(f"  ✅ Sources: {len(result.get('sources', []))} sources\n")
            
        except Exception as e:
            print(f"  ❌ FAILED: {e}\n")
            raise


def test_portfolio_queries():
    """Test portfolio-related queries."""
    print("\n=== Testing Portfolio Functionality ===\n")
    
    portfolio = {
        "AAPL": {"shares": 10, "price": 150},
        "GOOGL": {"shares": 5, "price": 100}
    }
    
    test_cases = [
        ("What is my portfolio worth?", portfolio, None),
        ("Analyze my portfolio", portfolio, None),
    ]
    
    for query, port, goals in test_cases:
        print(f"Query: '{query}'")
        try:
            result = process_query(query, portfolio=port, goals=goals)
            
            assert 'response' in result, "Missing 'response' key"
            assert len(result['response']) > 0, "Empty response"
            
            print(f"  ✅ Response: {len(result['response'])} chars")
            print(f"  ✅ Agents: {result.get('agents_used', [])}\n")
            
        except Exception as e:
            print(f"  ❌ FAILED: {e}\n")
            raise


def test_goals_queries():
    """Test goal-related queries."""
    print("\n=== Testing Goals Functionality ===\n")
    
    goals = [
        {"name": "Retirement", "amount": 1000000, "years": 30},
        {"name": "House", "amount": 500000, "years": 5}
    ]
    
    test_cases = [
        ("How can I reach my retirement goal?", None, goals),
    ]
    
    for query, port, goal_list in test_cases:
        print(f"Query: '{query}'")
        try:
            result = process_query(query, portfolio=port, goals=goal_list)
            
            assert 'response' in result, "Missing 'response' key"
            assert len(result['response']) > 0, "Empty response"
            
            print(f"  ✅ Response: {len(result['response'])} chars")
            print(f"  ✅ Agents: {result.get('agents_used', [])}\n")
            
        except Exception as e:
            print(f"  ❌ FAILED: {e}\n")
            raise


if __name__ == "__main__":
    print("=" * 60)
    print("INTEGRATION TEST - NO BREAKING CHANGES")
    print("=" * 60)
    
    try:
        test_basic_queries()
        test_portfolio_queries()
        test_goals_queries()
        
        print("=" * 60)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("=" * 60)
        print("\nConclusion:")
        print("- Basic queries: Working ✅")
        print("- Portfolio queries: Working ✅")
        print("- Goals queries: Working ✅")
        print("- Response structure: Unchanged ✅")
        print("- No breaking changes detected ✅")
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
