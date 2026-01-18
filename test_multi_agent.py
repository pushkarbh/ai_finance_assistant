"""
Test script to demonstrate multi-agent collaboration.
Shows how multiple agents work together to answer complex queries.
"""

from src.workflow.graph import process_query
from src.workflow.router import QueryRouter


def test_multi_agent_queries():
    """Test various queries that should trigger multiple agents."""
    
    test_cases = [
        {
            "query": "Analyze my portfolio and help me plan for retirement in 15 years",
            "expected_agents": ["portfolio_analysis", "goal_planning"],
            "description": "Portfolio analysis + retirement planning"
        },
        {
            "query": "I have $10,000 in stocks. How much should I save monthly to reach $1 million in 20 years?",
            "expected_agents": ["portfolio_analysis", "goal_planning"],
            "description": "Current portfolio + goal calculation"
        },
        {
            "query": "What's the current market situation and recent news?",
            "expected_agents": ["market_analysis", "news_synthesizer"],
            "description": "Market data + news synthesis"
        },
        {
            "query": "Check my portfolio performance and show me the latest market news",
            "expected_agents": ["portfolio_analysis", "news_synthesizer"],
            "description": "Portfolio review + news"
        }
    ]
    
    router = QueryRouter()
    
    print("=" * 80)
    print("MULTI-AGENT ROUTING TEST")
    print("=" * 80)
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        expected = test_case["expected_agents"]
        description = test_case["description"]
        
        print(f"Test {i}: {description}")
        print(f"Query: '{query}'")
        print(f"Expected agents: {expected}")
        
        # Get routed agents
        routed_agents = router.route(query)
        print(f"Routed agents: {routed_agents}")
        
        # Check if multi-agent
        is_multi = len(routed_agents) > 1
        print(f"Multi-agent: {'✅ YES' if is_multi else '❌ NO'}")
        
        # Verify expected agents are included
        matches = all(agent in routed_agents for agent in expected)
        print(f"Matches expected: {'✅ YES' if matches else '❌ NO'}")
        
        print("-" * 80)
        print()


def test_showcase_example():
    """
    Test the showcase example: Portfolio analysis + retirement planning
    This demonstrates true multi-agent collaboration.
    """
    
    print("=" * 80)
    print("MULTI-AGENT SHOWCASE EXAMPLE")
    print("=" * 80)
    print()
    
    # Sample portfolio data
    sample_portfolio = {
        "holdings": [
            {"ticker": "AAPL", "shares": 50, "purchase_price": 150.00},
            {"ticker": "MSFT", "shares": 30, "purchase_price": 280.00},
            {"ticker": "GOOGL", "shares": 20, "purchase_price": 120.00},
            {"ticker": "VTI", "shares": 100, "purchase_price": 200.00}
        ]
    }
    
    query = "Analyze my portfolio and help me plan for retirement in 15 years with a goal of $1 million"
    
    print(f"Query: {query}")
    print()
    print("Portfolio:")
    for holding in sample_portfolio["holdings"]:
        print(f"  - {holding['ticker']}: {holding['shares']} shares @ ${holding['purchase_price']}")
    print()
    print("Processing query through multi-agent workflow...")
    print("-" * 80)
    print()
    
    try:
        # Process the query
        result = process_query(
            query=query,
            portfolio=sample_portfolio
        )
        
        agents_used = result.get("agents_used", [])
        print(f"Agents used: {agents_used}")
        print(f"Multi-agent collaboration: {'✅ YES' if len(agents_used) > 1 else '❌ NO'}")
        print()
        
        if len(agents_used) > 1:
            print("🤝 MULTI-AGENT COLLABORATION SUCCESSFUL!")
            print()
            print("Individual agent outputs:")
            print("-" * 80)
            
            agent_outputs = result.get("agent_outputs", {})
            for agent_name, output in agent_outputs.items():
                print(f"\n{agent_name.upper()}:")
                print(output.get("response", "No response")[:200] + "...")
                print()
        
        print("-" * 80)
        print("FINAL SYNTHESIZED RESPONSE:")
        print("-" * 80)
        print(result.get("response", "No response"))
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n")
    
    # Test routing
    test_multi_agent_queries()
    
    print("\n" * 2)
    
    # Test full execution
    test_showcase_example()
    
    print("\n")
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
