# AI Finance Assistant - Architecture Documentation

## System Overview

The AI Finance Assistant is a multi-agent system built using LangGraph for workflow orchestration. It combines retrieval-augmented generation (RAG) for educational content with real-time market data integration.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │  Chat Tab   │ │ Portfolio   │ │  Market     │ │   Goals     │       │
│  │             │ │    Tab      │ │    Tab      │ │    Tab      │       │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘       │
│         │               │               │               │               │
│         └───────────────┴───────────────┴───────────────┘               │
│                                 │                                        │
│                    ┌────────────┴────────────┐                          │
│                    │   Streamlit Session     │                          │
│                    │       Management        │                          │
│                    └────────────┬────────────┘                          │
└─────────────────────────────────┼───────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼───────────────────────────────────────┐
│                        ORCHESTRATION LAYER                               │
│                                 │                                        │
│                    ┌────────────┴────────────┐                          │
│                    │   LangGraph Workflow    │                          │
│                    │      StateGraph         │                          │
│                    └────────────┬────────────┘                          │
│                                 │                                        │
│         ┌───────────────────────┼───────────────────────┐               │
│         │                       │                       │               │
│  ┌──────┴──────┐    ┌──────────┴──────────┐    ┌──────┴──────┐        │
│  │   Router    │    │  Agent Dispatcher   │    │  Aggregator │        │
│  │   Node      │ -> │      Nodes          │ -> │    Node     │        │
│  └─────────────┘    └─────────────────────┘    └─────────────┘        │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼───────────────────────────────────────┐
│                           AGENT LAYER                                    │
│                                 │                                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │ Finance QA   │ │  Portfolio   │ │   Market     │ │    Goal      │   │
│  │    Agent     │ │    Agent     │ │    Agent     │ │   Agent      │   │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘   │
│         │                │                │                │            │
│         │         ┌──────────────┐        │                │            │
│         │         │    News      │        │                │            │
│         │         │    Agent     │        │                │            │
│         │         └──────┬───────┘        │                │            │
└─────────┼────────────────┼────────────────┼────────────────┼────────────┘
          │                │                │                │
┌─────────┼────────────────┼────────────────┼────────────────┼────────────┐
│         │          DATA LAYER             │                │            │
│         │                │                │                │            │
│  ┌──────┴───────┐        │         ┌──────┴───────┐        │            │
│  │  RAG System  │        │         │   yFinance   │        │            │
│  │    (FAISS)   │        │         │     API      │        │            │
│  └──────┬───────┘        │         └──────────────┘        │            │
│         │                │                                  │            │
│  ┌──────┴───────┐        │                          ┌──────┴───────┐   │
│  │  Knowledge   │        │                          │  Projection  │   │
│  │    Base      │        │                          │    Engine    │   │
│  └──────────────┘        │                          └──────────────┘   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## LangGraph Workflow

### State Definition

```python
class AgentState(TypedDict):
    """Shared state across all agents in the workflow."""
    current_query: str           # User's input query
    session_id: str              # Unique session identifier
    messages: List               # Conversation history
    query_type: Optional[str]    # Classified query type
    target_agents: List[str]     # Agents selected by router
    agent_outputs: Dict          # Outputs from each agent
    portfolio: Optional[Dict]    # User's portfolio data
    goals: Optional[List]        # User's financial goals
    market_data: Optional[Dict]  # Cached market data
    sources: List[str]           # RAG sources used
    errors: List[str]            # Any errors encountered
    final_response: Optional[str] # Aggregated final response
```

### Graph Structure

```
                    ┌───────────────┐
                    │    START      │
                    └───────┬───────┘
                            │
                    ┌───────┴───────┐
                    │    Router     │
                    │     Node      │
                    └───────┬───────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
    ┌───────┴───────┐       │       ┌───────┴───────┐
    │  finance_qa   │       │       │   portfolio   │
    │     node      │       │       │     node      │
    └───────┬───────┘       │       └───────┬───────┘
            │               │               │
            │       ┌───────┴───────┐       │
            │       │    market     │       │
            │       │     node      │       │
            │       └───────┬───────┘       │
            │               │               │
            │       ┌───────┴───────┐       │
            │       │     goal      │       │
            │       │     node      │       │
            │       └───────┬───────┘       │
            │               │               │
            │       ┌───────┴───────┐       │
            │       │     news      │       │
            │       │     node      │       │
            │       └───────┬───────┘       │
            │               │               │
            └───────────────┼───────────────┘
                            │
                    ┌───────┴───────┐
                    │   Aggregator  │
                    │     Node      │
                    └───────┬───────┘
                            │
                    ┌───────┴───────┐
                    │      END      │
                    └───────────────┘
```

### Conditional Routing Logic

```python
def _select_agents(self, state: AgentState) -> List[str]:
    """Determine which agent nodes to execute."""
    target_agents = state.get("target_agents", [])

    if not target_agents:
        return ["finance_qa"]  # Default fallback

    return target_agents
```

## RAG System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      RAG PIPELINE                                │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Markdown    │ -> │   Document   │ -> │    Text      │      │
│  │   Files      │    │   Loader     │    │  Splitter    │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                │                 │
│                                                v                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │    Query     │ -> │  Embedding   │ -> │   Vector     │      │
│  │  Embedding   │    │    Model     │    │   Store      │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                                      │                 │
│         v                                      v                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Similarity  │ <- │    FAISS     │ <- │   Document   │      │
│  │   Search     │    │    Index     │    │   Chunks     │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                                                        │
│         v                                                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Retrieved   │ -> │   Context    │ -> │     LLM      │      │
│  │  Documents   │    │   Builder    │    │   Response   │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| Embedding Model | all-MiniLM-L6-v2 | Fast, lightweight embeddings |
| Chunk Size | 1000 | Characters per chunk |
| Chunk Overlap | 200 | Overlap for context continuity |
| Top K | 5 | Number of retrieved documents |
| Similarity Threshold | 0.7 | Minimum relevance score |

## Agent Specifications

### 1. Finance QA Agent

**Purpose**: Answer educational financial questions using RAG

**Input**:
- User query
- Retrieved context from knowledge base

**Output**:
- Educational response
- Source documents used

**Process Flow**:
```
Query -> Retrieve Context -> Build Prompt -> LLM -> Response
```

### 2. Portfolio Analysis Agent

**Purpose**: Analyze user portfolios and provide recommendations

**Input**:
- Portfolio holdings (CSV or JSON)
- User query

**Output**:
- Portfolio metrics (value, allocation, returns)
- Analysis and recommendations

**Calculations**:
- Total Portfolio Value: Σ(shares × current_price)
- Asset Allocation: (holding_value / total_value) × 100
- Return: ((current_value - cost_basis) / cost_basis) × 100

### 3. Market Analysis Agent

**Purpose**: Provide real-time market data and analysis

**Input**:
- Stock tickers from query
- Market data request type

**Output**:
- Current prices
- Market indices
- Historical trends

**Data Sources**:
- yFinance API for real-time data
- Caching layer (5-minute TTL)

### 4. Goal Planning Agent

**Purpose**: Help users plan and track financial goals

**Input**:
- Goal parameters (target, timeline, contributions)
- Current savings

**Output**:
- Projections
- Required contributions
- Progress tracking

**Formulas**:
```
Future Value = P × (1 + r)^n + PMT × [((1 + r)^n - 1) / r]

Where:
  P = Principal (current amount)
  r = Monthly return rate
  n = Number of months
  PMT = Monthly contribution
```

### 5. News Synthesizer Agent

**Purpose**: Aggregate and summarize financial news

**Input**:
- Topics/tickers from query
- Time range

**Output**:
- News summaries
- Market sentiment
- Key headlines

## Data Models

### Portfolio

```python
@dataclass
class PortfolioHolding:
    ticker: str
    shares: float
    purchase_price: float
    purchase_date: Optional[str] = None
    current_price: Optional[float] = None
```

### Financial Goal

```python
@dataclass
class FinancialGoal:
    name: str
    target_amount: float
    current_amount: float
    target_date: Optional[str] = None
    monthly_contribution: Optional[float] = None
    expected_return: float = 0.07
```

## API Integration

### OpenAI

```python
ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=2000,
    api_key=get_openai_api_key()
)
```

### yFinance

```python
# Stock data
ticker = yf.Ticker("AAPL")
info = ticker.info
history = ticker.history(period="1mo")
news = ticker.news
```

## Error Handling

### Strategy

1. **Agent-level**: Each agent catches and logs errors, returns graceful fallback
2. **Workflow-level**: Errors propagate to state.errors list
3. **UI-level**: Display user-friendly error messages

### Error Recovery

```python
try:
    result = agent.process(state)
except Exception as e:
    state["errors"].append(f"{agent.name}: {str(e)}")
    state["agent_outputs"][agent.name] = {
        "error": True,
        "message": "Unable to process request"
    }
```

## Performance Considerations

### Caching

| Cache | TTL | Purpose |
|-------|-----|---------|
| Stock Prices | 5 min | Reduce API calls |
| Market Summary | 5 min | Index data freshness |
| Embeddings | Persistent | FAISS index |

### Optimization

1. **Parallel Agent Execution**: Independent agents run concurrently
2. **Lazy Loading**: RAG index loaded on first use
3. **Connection Pooling**: Reuse LLM connections

## Security

### API Keys

- Stored in environment variables
- Never logged or exposed in UI
- Validated on startup

### Input Validation

- Portfolio data sanitized
- Query length limits
- Ticker symbol validation

## Testing Strategy

### Unit Tests

- Individual agent logic
- RAG retrieval accuracy
- State management
- Utility functions

### Integration Tests

- End-to-end workflow
- Multi-agent coordination
- Error propagation

### Coverage Target: 80%+

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    HuggingFace Spaces                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  Streamlit Container                   │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │  │
│  │  │   App.py    │  │  FAISS      │  │  Knowledge  │   │  │
│  │  │  (8501)     │  │  Index      │  │    Base     │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘   │  │
│  └───────────────────────────────────────────────────────┘  │
│                              │                               │
│                              v                               │
│                      Environment Variables                   │
│                      - OPENAI_API_KEY                       │
│                      - ALPHA_VANTAGE_API_KEY                │
└─────────────────────────────────────────────────────────────┘
                               │
                               v
              ┌────────────────┴────────────────┐
              │                                 │
        ┌─────┴─────┐                    ┌─────┴─────┐
        │  OpenAI   │                    │ yFinance  │
        │    API    │                    │    API    │
        └───────────┘                    └───────────┘
```
