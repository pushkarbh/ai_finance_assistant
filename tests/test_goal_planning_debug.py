"""Test goal planning agent with debug output."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.state import create_initial_state
from workflow.graph import FinanceAssistantWorkflow

def test_goal_planning():
    """Test goal planning query."""
    query = "Help me reach $1M in 15 years with $150K in 401K while maxing out contributions"
    
    print(f"Testing query: {query}")
    print("-" * 80)
    
    # Create graph
    workflow = FinanceAssistantWorkflow()
    
    # Create initial state
    state = create_initial_state(query, session_id="test-debug")
    
    # Run the workflow
    print("\nRunning workflow...")
    result = workflow.app.invoke(state)
    
    print("\n" + "=" * 80)
    print("FINAL RESPONSE:")
    print("=" * 80)
    print(result.get("final_response", "NO RESPONSE"))
    print("\n" + "=" * 80)
    print("AGENT OUTPUTS:")
    print("=" * 80)
    for agent_name, output in result.get("agent_outputs", {}).items():
        print(f"\n{agent_name}:")
        print(f"  Response: {output.get('response', 'N/A')[:200]}...")
    
    print("\n" + "=" * 80)
    print("ERRORS:")
    print("=" * 80)
    errors = result.get("errors", [])
    if errors:
        for error in errors:
            print(f"  - {error}")
    else:
        print("  No errors")

if __name__ == "__main__":
    test_goal_planning()
