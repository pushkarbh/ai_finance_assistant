from src.workflow.router import route_query

# Test queries
queries = [
    'Help me find how can I reach $1M in 15 years if I have 150,000 in 401K and planning to max out on 401k each year',
    'Help me plan my goal to reach $1 million dollars in 15 yrs with 150K in current retirement savings while contributing 1800 dollars each month',
    'How is Apple doing',
    'Analyze my portfolio'
]

for q in queries:
    agents = route_query(q)
    print(f'Query: {q[:70]}...')
    print(f'Agents: {agents}')
    print()
