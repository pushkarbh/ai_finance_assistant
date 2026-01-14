# AI Finance Assistant - Future Enhancements

This document outlines potential improvements and additional features for the AI Finance Assistant.

---

## 1. Guardrails & Safety

### Input Guardrails
- [ ] **Query validation** - Detect and filter inappropriate/off-topic queries
- [ ] **PII detection** - Warn users before they share sensitive information (SSN, account numbers)
- [ ] **Prompt injection protection** - Detect attempts to manipulate agent behavior
- [ ] **Rate limiting** - Prevent abuse with query rate limits per session

### Off-Topic / Irrelevant Query Filtering
The assistant should only respond to finance-related queries and politely decline non-finance topics.

#### Queries to ACCEPT (Finance-Related)
- Investment questions: "What are ETFs?", "How do bonds work?"
- Portfolio queries: "Analyze my holdings", "Am I diversified enough?"
- Market questions: "What's AAPL trading at?", "How's the S&P doing?"
- Goal planning: "How much should I save for retirement?"
- Tax questions: "How are RSUs taxed?", "What's a 401k?"
- General finance: "What's compound interest?", "Explain dollar-cost averaging"

#### Queries to REJECT (Off-Topic)
- Sports: "Who won the US Open men's final?"
- Weather: "Is it going to rain this week?"
- Entertainment: "What movies are playing?", "Who won the Oscars?"
- General knowledge: "What's the capital of France?", "How tall is Mount Everest?"
- Recipes: "How do I make pasta?"
- Tech support: "How do I reset my iPhone?"
- News (non-financial): "What's happening in politics?"

#### Implementation Options

**Option 1: Keyword + LLM Classifier**
```python
class TopicFilter:
    FINANCE_KEYWORDS = [
        'stock', 'bond', 'etf', 'invest', 'portfolio', 'market', 'dividend',
        'retirement', '401k', 'ira', 'roth', 'tax', 'capital gains', 'rsu',
        'savings', 'compound interest', 'diversification', 'risk', 'return',
        'mutual fund', 'index fund', 'broker', 'trading', 'asset', 'equity',
        'financial', 'money', 'wealth', 'budget', 'debt', 'loan', 'mortgage',
        'interest rate', 'inflation', 'fed', 'economy', 'gdp', 'earnings',
        'p/e ratio', 'market cap', 'bull', 'bear', 'volatility', 'hedge',
        'crypto', 'bitcoin', 'dollar', 'currency', 'forex', 'options'
    ]

    def is_finance_related(self, query: str) -> tuple[bool, str]:
        query_lower = query.lower()

        # Quick keyword check
        if any(kw in query_lower for kw in self.FINANCE_KEYWORDS):
            return True, "keyword_match"

        # LLM-based classification for ambiguous queries
        return self._llm_classify(query)

    def _llm_classify(self, query: str) -> tuple[bool, str]:
        prompt = f"""Is this query related to finance, investing, or money management?
Query: "{query}"
Answer only YES or NO."""
        # Use fast/cheap model for classification
        response = llm.invoke(prompt)
        return response.strip().upper() == "YES", "llm_classified"
```

**Option 2: Intent Classification Model**
```python
from transformers import pipeline

classifier = pipeline("zero-shot-classification")
labels = ["finance", "sports", "weather", "entertainment", "general"]

def classify_query(query: str) -> str:
    result = classifier(query, labels)
    return result["labels"][0]  # Top predicted label
```

**Option 3: Router Enhancement**
```python
# Add to QueryRouter
def route(self, query: str) -> dict:
    # First check if query is on-topic
    if not self.is_finance_related(query):
        return {
            "agents": [],
            "query_type": "off_topic",
            "response": self._get_polite_decline()
        }
    # ... normal routing
```

#### Polite Decline Responses
```python
OFF_TOPIC_RESPONSES = [
    "I'm a financial education assistant, so I focus on topics like investing, "
    "portfolio management, and financial planning. Is there anything finance-related "
    "I can help you with?",

    "That's outside my area of expertise! I specialize in financial topics like "
    "stocks, bonds, retirement planning, and investment strategies. "
    "What financial questions can I answer for you?",

    "I'm designed to help with finance and investing questions. "
    "Feel free to ask me about ETFs, portfolio diversification, retirement accounts, "
    "or any other money-related topics!",
]
```

#### Edge Cases to Handle
- [ ] **Ambiguous queries**: "What's Apple doing?" (stock vs company news)
- [ ] **Finance-adjacent**: "Should I buy a house?" (real estate = somewhat relevant)
- [ ] **Mixed queries**: "Will the election affect my stocks?" (politics + finance)
- [ ] **Greetings**: "Hello" / "Hi" (should respond politely, ask how to help)
- [ ] **Meta questions**: "What can you do?" (should explain capabilities)

#### Configuration
```yaml
# config.yaml
guardrails:
  topic_filter:
    enabled: true
    strict_mode: false  # If true, reject ambiguous queries
    allowed_topics:
      - finance
      - investing
      - economics
      - real_estate  # Optional: include adjacent topics
    log_rejected: true  # Log off-topic queries for analysis
```

### Output Guardrails
- [ ] **Financial disclaimer injection** - Automatically append "not financial advice" disclaimers
- [ ] **Hallucination detection** - Cross-validate LLM outputs against RAG sources
- [ ] **Confidence scoring** - Display confidence levels for responses
- [ ] **Fact-checking layer** - Validate numerical claims (stock prices, calculations)
- [ ] **Toxic content filtering** - Ensure responses are professional and appropriate

### Domain-Specific Guardrails
- [ ] **Investment advice boundaries** - Detect when queries cross into regulated advice territory
- [ ] **Risk warnings** - Auto-inject warnings for high-risk investment discussions
- [ ] **Source attribution enforcement** - Require citations for factual claims
- [ ] **Regulatory compliance checks** - Flag content that might violate SEC/FINRA guidelines

### Implementation Options
- [ ] Evaluate **NeMo Guardrails** (NVIDIA) for rail-based guardrails
- [ ] Evaluate **Guardrails AI** library for output validation
- [ ] Custom LLM-based classifier for domain-specific checks
- [ ] Rule-based filters for known patterns

---

## 2. Additional Agents

### Tax Planning Agent (Stretch Goal)
- [ ] Tax-loss harvesting recommendations
- [ ] Capital gains calculations (short-term vs long-term)
- [ ] Tax bracket optimization strategies
- [ ] RSU/ESPP tax implications
- [ ] Retirement account contribution optimization

### Risk Assessment Agent
- [ ] Portfolio risk scoring (beta, volatility, VaR)
- [ ] Correlation analysis between holdings
- [ ] Stress testing against historical scenarios
- [ ] Risk-adjusted return metrics (Sharpe, Sortino)

### Rebalancing Agent
- [ ] Target allocation tracking
- [ ] Drift detection and alerts
- [ ] Tax-efficient rebalancing suggestions
- [ ] Automatic rebalancing recommendations

---

## 3. Memory & Personalization

### LangGraph Managed Conversation History
Use LangGraph's built-in checkpointing and memory management for conversation persistence.

#### Core Features
- [ ] **Message history in state** - Store conversation messages in AgentState
- [ ] **Checkpointer integration** - Use LangGraph's checkpointer for persistence
- [ ] **Thread-based conversations** - Separate conversation threads per session
- [ ] **Memory across turns** - Maintain context for follow-up questions
- [ ] **Conversation summarization** - Compress long histories to stay within token limits

#### Implementation
```python
from langgraph.graph import StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage

# Option 1: In-memory (development)
memory = MemorySaver()

# Option 2: SQLite persistence (production)
memory = SqliteSaver.from_conn_string("conversations.db")

# Option 3: PostgreSQL (scalable)
from langgraph.checkpoint.postgres import PostgresSaver
memory = PostgresSaver.from_conn_string(os.environ["DATABASE_URL"])

# Compile graph with checkpointer
app = graph.compile(checkpointer=memory)

# Invoke with thread_id for conversation continuity
config = {"configurable": {"thread_id": session_id}}
result = app.invoke(state, config)

# Messages automatically persisted and restored
```

#### State Schema Update
```python
from typing import Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Use add_messages reducer for automatic message management
    messages: Annotated[list, add_messages]
    current_query: str
    session_id: str
    # ... other fields
```

#### Features to Implement
- [ ] **Thread management** - Create/resume conversation threads
- [ ] **History retrieval** - Get past N messages for context
- [ ] **Selective memory** - Remember important facts (portfolio, goals)
- [ ] **Conversation history UI** - View past conversations (what was asked & answered)
- [ ] **Incremental response revision** - When user adds tickers to portfolio, revise response incrementally instead of regenerating from scratch
- [ ] **Delta detection** - Detect what changed in input and only reprocess affected parts
- [ ] **Memory window** - Sliding window to limit context size
- [ ] **Summary memory** - Summarize old messages to compress history
- [ ] **Cross-session memory** - Remember user across different sessions

#### Conversation Flow Example
```
User: "What are ETFs?"
Assistant: "ETFs are exchange-traded funds that..."

User: "How do they compare to mutual funds?"  # Follow-up
Assistant: "Compared to the ETFs I just explained..."  # Has context!

User: "Which would be better for my portfolio?"  # References portfolio
Assistant: "Given your portfolio with AAPL, MSFT..."  # Remembers portfolio
```

#### Storage Options Comparison
| Backend | Persistence | Scalability | Use Case |
|---------|-------------|-------------|----------|
| MemorySaver | No | Single process | Development |
| SqliteSaver | Yes | Single instance | Local deployment |
| PostgresSaver | Yes | Multi-instance | Production |
| RedisSaver | Yes | Multi-instance | High performance |

### Conversation Memory
- [ ] Persist conversation history across sessions
- [ ] Implement memory summarization for long conversations
- [ ] User preference learning (risk tolerance, investment style)
- [ ] Context carryover between related queries

### User Profiles
- [ ] Save user financial profiles
- [ ] Remember portfolio data between sessions
- [ ] Track goal progress over time
- [ ] Personalized recommendations based on history

### Storage Options
- [ ] SQLite for local persistence
- [ ] Redis for session caching
- [ ] Vector store for semantic memory search

---

## 4. Enhanced RAG Capabilities

### Knowledge Base Expansion
- [ ] Add more financial education content (target: 50-100 articles)
- [ ] Include regulatory documents (IRS publications, SEC guides)
- [ ] Add real-world case studies
- [ ] Integrate financial glossary with cross-references
- [ ] **Web scraper for articles** - Download content from Investopedia, NerdWallet, etc.

#### Article Scraper Implementation
```python
# scraper.py - Download financial education articles
import requests
from bs4 import BeautifulSoup
import time

SOURCES = {
    "investopedia": "https://www.investopedia.com/",
    "nerdwallet": "https://www.nerdwallet.com/",
    "thebalance": "https://www.thebalancemoney.com/",
}

class FinanceArticleScraper:
    def scrape_investopedia(self, topic: str) -> list[dict]:
        """Scrape articles from Investopedia."""
        # Respect robots.txt and rate limits
        time.sleep(1)
        # ... implementation

    def save_to_knowledge_base(self, articles: list[dict]):
        """Save scraped articles to knowledge base as markdown."""
        for article in articles:
            filename = f"src/data/knowledge_base/{article['slug']}.md"
            with open(filename, 'w') as f:
                f.write(f"# {article['title']}\n\n")
                f.write(f"*Source: {article['source']}*\n\n")
                f.write(article['content'])
```

### RAG Improvements
- [ ] Hybrid search (keyword + semantic)
- [ ] Re-ranking with cross-encoder
- [ ] Query expansion for better retrieval
- [ ] Multi-hop reasoning for complex questions
- [ ] Source quality scoring
- [ ] **Show citations in responses** - Display source documents when data is pulled from RAG

#### RAG Citations Display
```python
# In response rendering
def display_response_with_citations(response: dict):
    st.markdown(response["answer"])

    if response.get("sources"):
        with st.expander("📚 Sources"):
            for source in response["sources"]:
                st.markdown(f"- **{source['title']}** ({source['file']})")
                st.caption(f"Relevance: {source['score']:.2f}")
```

### Dynamic Knowledge
- [ ] Periodic knowledge base updates
- [ ] Integration with financial news feeds
- [ ] Market condition-aware responses

---

## 5. Observability & Monitoring

### Logging & Tracing
- [ ] Structured logging with correlation IDs
- [ ] LangSmith integration for LLM tracing (optional but recommended)
- [ ] Request/response logging (sanitized)
- [ ] Agent execution timeline visualization
- [ ] **Live agent execution log in UI** - Show which agents are running in real-time (essential for HuggingFace Spaces demo)

#### Agent Execution Log (HuggingFace Spaces)
```python
# Display live log of agent execution
import streamlit as st

def render_agent_log():
    """Show real-time log of which agents are processing."""
    log_container = st.empty()

    # Update log as agents execute
    with log_container.container():
        st.markdown("### 🔄 Processing Log")
        for entry in st.session_state.get("agent_log", []):
            icon = "✅" if entry["status"] == "complete" else "⏳"
            st.markdown(f"{icon} **{entry['agent']}** - {entry['message']}")
            st.caption(f"Time: {entry['duration']:.2f}s")

# In workflow execution
def log_agent_start(agent_name: str):
    if "agent_log" not in st.session_state:
        st.session_state.agent_log = []
    st.session_state.agent_log.append({
        "agent": agent_name,
        "status": "running",
        "message": "Processing...",
        "start_time": time.time()
    })

def log_agent_complete(agent_name: str, message: str):
    for entry in st.session_state.agent_log:
        if entry["agent"] == agent_name and entry["status"] == "running":
            entry["status"] = "complete"
            entry["message"] = message
            entry["duration"] = time.time() - entry["start_time"]
```

#### LangSmith Integration (Optional)
```python
# Enable LangSmith tracing
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-langsmith-api-key"
os.environ["LANGCHAIN_PROJECT"] = "ai-finance-assistant"

# All LangChain/LangGraph operations automatically traced
```

### Metrics
- [ ] Response latency tracking
- [ ] Token usage monitoring
- [ ] Agent selection distribution
- [ ] RAG retrieval quality metrics
- [ ] Error rate tracking

### Dashboards
- [ ] Usage analytics dashboard
- [ ] Cost tracking (API usage)
- [ ] Query categorization insights
- [ ] User satisfaction metrics

### LangGraph Visualization
- [ ] **State graph diagram** - Visual representation of the workflow graph
- [ ] **Real-time execution view** - Show which node is currently executing
- [ ] **State inspection** - Display current state at each node during execution
- [ ] **Edge highlighting** - Show which path was taken through the graph
- [ ] **Export to Mermaid/PNG** - Generate shareable diagrams for documentation

Implementation options:
```python
# Option 1: Built-in Mermaid export
from langgraph.graph import StateGraph
graph = workflow.graph
print(graph.get_graph().draw_mermaid())

# Option 2: PNG image generation (requires pygraphviz or grandalf)
graph.get_graph().draw_mermaid_png(output_file_path="workflow_graph.png")

# Option 3: Display in Streamlit
import streamlit as st
mermaid_code = graph.get_graph().draw_mermaid()
st.markdown(f"```mermaid\n{mermaid_code}\n```")

# Option 4: Interactive visualization with streamlit-agraph
from streamlit_agraph import agraph, Node, Edge, Config
nodes = [Node(id=n, label=n) for n in graph.nodes]
edges = [Edge(source=e[0], target=e[1]) for e in graph.edges]
agraph(nodes=nodes, edges=edges, config=Config())
```

Use cases:
- **Documentation**: Auto-generate architecture diagrams for README
- **Debugging**: See which agents were invoked for a query
- **Demo**: Show the multi-agent orchestration visually during presentation
- **Monitoring**: Display real-time workflow execution in admin panel

---

## 6. Advanced Portfolio Features

### Analysis
- [ ] Sector/industry breakdown visualization
- [ ] Geographic exposure analysis
- [ ] Dividend yield tracking
- [ ] P/E ratio comparisons
- [ ] Historical performance charts

### Import/Export
- [ ] Support for brokerage CSV formats (Fidelity, Schwab, Vanguard)
- [ ] Portfolio export functionality
- [ ] Integration with financial aggregators (Plaid)

### Alerts
- [ ] Price alert notifications
- [ ] Portfolio drift alerts
- [ ] Goal milestone notifications
- [ ] Dividend payment reminders

---

## 7. UI/UX Improvements

### Interface
- [ ] **Modern UI Redesign** - Create a simple, intuitive web-like experience
  - [ ] Bright color scheme with high contrast for visual clarity
  - [ ] Distinct visual separation between UI sections (cards, borders, backgrounds)
  - [ ] Modern icon set (consider Lucide, Heroicons, or Streamlit's built-in icons)
  - [ ] Clean typography with clear hierarchy
  - [ ] Consistent spacing and alignment
  - [ ] Prominent CTAs with clear visual feedback
  - [ ] Responsive layout that works across screen sizes
- [ ] Dark mode support
- [ ] Mobile-responsive design
- [ ] Keyboard shortcuts
- [ ] Chat history sidebar
- [ ] Export conversation to PDF

### Loading Experience - Financial Wisdom
- [ ] **Rotating finance quotes** - Display famous investor quotes while waiting for LLM
- [ ] **Financial principles** - Show educational tips during loading (e.g., "Rule of 72", "Pay yourself first")
- [ ] **Did you know?** - Random financial facts to keep users engaged
- [ ] **Progress indicators** - Show which agent is processing with relevant tips
- [ ] **Contextual tips** - Match loading messages to query type (portfolio query → diversification tip)

Example quotes to include:
- "The stock market is a device for transferring money from the impatient to the patient." - Warren Buffett
- "Do not save what is left after spending, but spend what is left after saving." - Warren Buffett
- "An investment in knowledge pays the best interest." - Benjamin Franklin
- "The four most dangerous words in investing are: 'This time it's different.'" - Sir John Templeton
- "Price is what you pay. Value is what you get." - Warren Buffett
- "Compound interest is the eighth wonder of the world." - Albert Einstein (attributed)
- "The best time to plant a tree was 20 years ago. The second best time is now." - Chinese Proverb

Financial principles to rotate:
- Rule of 72: Divide 72 by your interest rate to estimate years to double your money
- Emergency fund: Aim for 3-6 months of expenses in liquid savings
- 50/30/20 Rule: 50% needs, 30% wants, 20% savings
- Dollar-cost averaging reduces timing risk
- Diversification is the only free lunch in investing

### Loading Animation
- [ ] **Animated spinner/loader** - Visual indicator that processing is in progress
- [ ] **Progress bar animation** - Indeterminate progress bar during LLM calls
- [ ] **Pulsing icon** - Subtle pulsing effect on the assistant avatar
- [ ] **Typing indicator** - "Assistant is thinking..." with animated dots
- [ ] **Multi-stage progress** - Show stages: "Routing query..." → "Retrieving context..." → "Generating response..."
- [ ] **Cancel button** - Allow users to cancel long-running requests
- [ ] **Timeout handling** - Graceful message if processing takes too long

Implementation options for Streamlit:
```python
# Option 1: Built-in spinner (current)
with st.spinner("Thinking..."):
    result = process_query(query)

# Option 2: Custom animated component
with st.status("Processing your question...", expanded=True) as status:
    st.write("🔍 Analyzing query...")
    time.sleep(0.5)
    st.write("📚 Searching knowledge base...")
    # ... LLM call
    status.update(label="Complete!", state="complete")

# Option 3: Lottie animation (requires streamlit-lottie)
from streamlit_lottie import st_lottie
st_lottie(animation_json, height=150, key="loading")

# Option 4: Custom CSS animation
st.markdown('''
<style>
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
.thinking { animation: pulse 1.5s infinite; }
</style>
<div class="thinking">🤔 Analyzing your question...</div>
''', unsafe_allow_html=True)
```

Animation should:
- Start immediately when user submits query
- Show activity so user knows system is working
- Display rotating quotes/tips alongside animation
- Stop and clear when response is ready
- Handle errors gracefully (show error state, not infinite spinner)

### Visualization
- [ ] Interactive portfolio charts (Plotly)
- [ ] Goal progress gauges
- [ ] Market heatmaps
- [ ] Comparison charts

### Portfolio Analysis & Performance Visualization
Rich visualizations for portfolio analysis and risk assessment.

#### Portfolio Visualizations
- [ ] **Pie chart** - Asset allocation by sector/type
- [ ] **Treemap** - Holdings sized by value, colored by performance
- [ ] **Bar chart** - Individual holding performance (gain/loss)
- [ ] **Line chart** - Portfolio value over time
- [ ] **Stacked area** - Allocation changes over time
- [ ] **Correlation matrix** - Heatmap of holding correlations

#### Risk Analysis Visualizations
- [ ] **Risk/Return scatter** - Holdings plotted by risk vs return
- [ ] **Volatility chart** - Historical volatility of portfolio
- [ ] **Drawdown chart** - Maximum drawdown visualization
- [ ] **VaR gauge** - Value at Risk indicator
- [ ] **Beta comparison** - Portfolio beta vs benchmark

#### Implementation Examples
```python
import plotly.express as px
import plotly.graph_objects as go

def render_portfolio_allocation(holdings: list):
    """Pie chart of portfolio allocation."""
    fig = px.pie(
        holdings,
        values='current_value',
        names='ticker',
        title='Portfolio Allocation',
        hole=0.4  # Donut chart
    )
    st.plotly_chart(fig, use_container_width=True)

def render_performance_bar(holdings: list):
    """Bar chart of individual holding performance."""
    fig = px.bar(
        holdings,
        x='ticker',
        y='gain_loss_pct',
        color='gain_loss_pct',
        color_continuous_scale=['red', 'yellow', 'green'],
        title='Holding Performance (%)'
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    st.plotly_chart(fig, use_container_width=True)

def render_risk_return_scatter(holdings: list):
    """Scatter plot of risk vs return."""
    fig = px.scatter(
        holdings,
        x='volatility',
        y='return_pct',
        size='current_value',
        color='sector',
        hover_name='ticker',
        title='Risk vs Return'
    )
    st.plotly_chart(fig, use_container_width=True)

def render_portfolio_treemap(holdings: list):
    """Treemap showing holdings sized by value, colored by performance."""
    fig = px.treemap(
        holdings,
        path=['sector', 'ticker'],
        values='current_value',
        color='gain_loss_pct',
        color_continuous_scale='RdYlGn',
        title='Portfolio Treemap'
    )
    st.plotly_chart(fig, use_container_width=True)

def render_correlation_heatmap(correlation_matrix):
    """Heatmap of holding correlations."""
    fig = px.imshow(
        correlation_matrix,
        labels=dict(color="Correlation"),
        color_continuous_scale='RdBu',
        title='Holdings Correlation Matrix'
    )
    st.plotly_chart(fig, use_container_width=True)
```

#### Dashboard Layout
```
┌─────────────────────────────────────────────────────────────┐
│  Portfolio Summary                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ $125,432 │ │  +12.5%  │ │ 8 stocks │ │  Medium  │       │
│  │  Value   │ │  Return  │ │ Holdings │ │   Risk   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │   Allocation Pie    │  │  Performance Bars   │          │
│  │        (40%)        │  │       (60%)         │          │
│  └─────────────────────┘  └─────────────────────┘          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Portfolio Value Over Time                  │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │   Risk/Return       │  │  Sector Treemap     │          │
│  │    Scatter          │  │                     │          │
│  └─────────────────────┘  └─────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### Technical Summary Tab (Demo Showcase)
A dedicated tab or sidebar section to showcase the technical architecture - perfect for demos and interviews.

#### Content to Display
- [ ] **Project Overview** - Brief description, tech stack badges, version info
- [ ] **Architecture Diagram** - High-level system architecture (Mermaid or image)
- [ ] **LangGraph State Graph** - Interactive visualization of the workflow nodes
- [ ] **Agent Registry** - List of all agents with descriptions and capabilities
- [ ] **RAG Pipeline** - Visual representation of document → embedding → retrieval flow
- [ ] **Tech Stack** - LangGraph, OpenAI, FAISS, Streamlit, yFinance with version info
- [ ] **Knowledge Base Stats** - Number of documents, chunks, topics covered

#### Live Workflow Animation (Wow Factor)
- [ ] **Real-time node highlighting** - Animate which LangGraph node is active during query processing
- [ ] **Execution path trace** - Show the path taken through the graph with animated edges
- [ ] **State transitions** - Display state changes as they happen
- [ ] **Agent activity indicators** - Pulsing/glowing effect on active agent node
- [ ] **Timing breakdown** - Show time spent in each node

Implementation approach for live animation:
```python
# Using callbacks to track node execution
from langgraph.graph import StateGraph

class AnimatedWorkflow:
    def __init__(self, ui_callback):
        self.ui_callback = ui_callback  # Function to update UI

    def run_with_animation(self, query):
        # Notify UI: Starting router
        self.ui_callback("route", "active")
        result = self.router.route(query)
        self.ui_callback("route", "complete")

        # Notify UI: Starting agent
        for agent in result.agents:
            self.ui_callback(agent, "active")
            output = self.agents[agent].process(state)
            self.ui_callback(agent, "complete")

        return final_response

# Streamlit UI with session state for animation
import streamlit as st
import time

def render_animated_graph():
    # Create placeholder for graph
    graph_placeholder = st.empty()

    # Node states: "pending", "active", "complete"
    node_states = st.session_state.get("node_states", {})

    # Generate Mermaid with conditional styling
    mermaid = generate_mermaid_with_highlights(node_states)
    graph_placeholder.markdown(f"```mermaid\n{mermaid}\n```")

# CSS for node animations
st.markdown('''
<style>
@keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.1); opacity: 0.8; }
}
.node-active { animation: pulse 0.8s infinite; fill: #4CAF50 !important; }
.node-complete { fill: #2196F3 !important; }
.node-pending { fill: #9E9E9E !important; }
.edge-active { stroke: #4CAF50 !important; stroke-width: 3px; }
</style>
''', unsafe_allow_html=True)
```

Alternative: Use `streamlit-agraph` for interactive graph with live updates:
```python
from streamlit_agraph import agraph, Node, Edge, Config

def render_live_graph(active_node=None):
    nodes = [
        Node(id="route", label="Router",
             color="#4CAF50" if active_node == "route" else "#gray"),
        Node(id="finance_qa", label="Finance QA",
             color="#4CAF50" if active_node == "finance_qa" else "#gray"),
        Node(id="portfolio", label="Portfolio",
             color="#4CAF50" if active_node == "portfolio" else "#gray"),
        # ... other nodes
    ]
    edges = [
        Edge(source="route", target="finance_qa"),
        Edge(source="route", target="portfolio"),
        # ... other edges
    ]
    config = Config(directed=True, physics=False, hierarchical=True)
    return agraph(nodes=nodes, edges=edges, config=config)
```

#### UI Layout Options
```
Option 1: New Tab
┌─────────────────────────────────────────────────────────┐
│  💬 Chat  │  📊 Portfolio  │  📈 Market  │  🎯 Goals  │  🔧 Technical  │
└─────────────────────────────────────────────────────────┘

Option 2: Sidebar Section
┌──────────────┬──────────────────────────────────────────┐
│  [Sidebar]   │                                          │
│              │         Main Content                     │
│  📊 Stats    │                                          │
│  🔧 Tech     │                                          │
│  └─ Graph    │                                          │
│  └─ Agents   │                                          │
└──────────────┴──────────────────────────────────────────┘

Option 3: Expandable Panel (in Chat tab)
┌─────────────────────────────────────────────────────────┐
│  [▶ Show Technical Details]                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │  LangGraph Workflow        │  Current Query     │   │
│  │  ┌─────┐                   │  Status: Processing│   │
│  │  │Route│ ──► [Agent] ──►   │  Active: finance_qa│   │
│  │  └─────┘                   │  Time: 1.2s        │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Accessibility
- [ ] Screen reader support
- [ ] High contrast mode
- [ ] Font size adjustments

---

## 8. Testing & Quality

### Test Coverage
- [ ] Achieve 90%+ code coverage
- [ ] Add property-based testing (Hypothesis)
- [ ] Load testing for concurrent users
- [ ] Chaos testing for error scenarios

### Quality Assurance
- [ ] LLM response evaluation framework
- [ ] RAG retrieval accuracy benchmarks
- [ ] A/B testing infrastructure
- [ ] User feedback collection

---

## 9. Deployment & DevOps

### CI/CD
- [ ] GitHub Actions workflow
- [ ] Automated testing on PR
- [ ] Staging environment
- [ ] Blue-green deployments

### Infrastructure
- [ ] Docker containerization (see detailed section below)
- [ ] Kubernetes deployment option
- [ ] Auto-scaling configuration
- [ ] Health check endpoints

### HuggingFace Spaces Deployment
- [ ] **FAISS index loading script** - Ensure FAISS index loads correctly on HF Spaces
- [ ] **API keys via UI** - Allow users to enter API keys directly in the UI (instead of .env)
- [ ] **Fallback for missing index** - Auto-create index if not found

#### FAISS Loading for HuggingFace
```python
# scripts/load_faiss_hf.py - Load FAISS index on HuggingFace Spaces
import os
from pathlib import Path

def ensure_faiss_index():
    """Ensure FAISS index exists, create if missing."""
    index_path = Path("data/faiss_index")

    if not index_path.exists():
        print("FAISS index not found, creating...")
        from src.rag.vector_store import VectorStoreManager
        from src.rag.document_processor import load_and_process_documents

        docs = load_and_process_documents()
        manager = VectorStoreManager()
        manager.create_index(docs, save=True)
        print("FAISS index created successfully!")
    else:
        print("FAISS index found, loading...")

# Call on app startup
ensure_faiss_index()
```

#### API Keys in UI (Alternative to .env)
```python
# Allow users to enter API keys directly in the UI
import streamlit as st

def get_api_keys():
    """Get API keys from UI or environment."""
    with st.sidebar:
        st.markdown("### 🔑 API Configuration")

        # Check if keys exist in environment first
        openai_key = os.environ.get("OPENAI_API_KEY", "")

        if not openai_key:
            openai_key = st.text_input(
                "OpenAI API Key",
                type="password",
                help="Enter your OpenAI API key. Get one at https://platform.openai.com/"
            )

            if openai_key:
                os.environ["OPENAI_API_KEY"] = openai_key
                st.success("API key configured!")
            else:
                st.warning("Please enter your OpenAI API key to use the assistant.")
                st.stop()

        return openai_key

# Call at app startup
api_key = get_api_keys()
```

#### HuggingFace Spaces Requirements
```
# requirements.txt additions for HF Spaces
huggingface_hub
spaces
```

#### app.py Header for HF Spaces
```python
# Required for HuggingFace Spaces
import spaces  # Optional: for GPU support

# Ensure index exists before app loads
from scripts.load_faiss_hf import ensure_faiss_index
ensure_faiss_index()
```

### Dockerization (Complete Container Setup)

#### Core Files to Create
- [ ] **Dockerfile** - Multi-stage build for optimized image
- [ ] **docker-compose.yml** - Full stack with all services
- [ ] **.dockerignore** - Exclude unnecessary files
- [ ] **docker-compose.dev.yml** - Development overrides with hot reload
- [ ] **docker-compose.prod.yml** - Production configuration

#### Dockerfile Structure
```dockerfile
# Dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Production stage
FROM python:3.11-slim as production

WORKDIR /app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Copy wheels and install
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application code
COPY src/ ./src/
COPY config.yaml .
COPY run.py .
COPY scripts/ ./scripts/

# Initialize RAG index at build time (optional)
# RUN python scripts/init_rag.py

# Set ownership
RUN chown -R appuser:appuser /app
USER appuser

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the application
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
CMD ["streamlit", "run", "src/web_app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### Docker Compose Setup
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ALPHA_VANTAGE_API_KEY=${ALPHA_VANTAGE_API_KEY}
      - STREAMLIT_SERVER_HEADLESS=true
    volumes:
      - faiss_index:/app/data/faiss_index
      - ./src/data/knowledge_base:/app/src/data/knowledge_base:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Optional: Redis for caching (future enhancement)
  # redis:
  #   image: redis:alpine
  #   ports:
  #     - "6379:6379"
  #   volumes:
  #     - redis_data:/data

volumes:
  faiss_index:
  # redis_data:
```

#### Development Setup with Hot Reload
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEBUG=true
    volumes:
      - ./src:/app/src  # Hot reload
      - ./config.yaml:/app/config.yaml
    command: streamlit run src/web_app/app.py --server.runOnSave=true
```

#### Tasks
- [ ] **Create Dockerfile** - Multi-stage build for small image size
- [ ] **Create .dockerignore** - Exclude venv, __pycache__, .git, tests, etc.
- [ ] **Create docker-compose.yml** - Main orchestration file
- [ ] **Environment variables** - Secure handling of API keys via .env
- [ ] **Volume mounts** - Persist FAISS index, mount knowledge base
- [ ] **Health checks** - Ensure container health monitoring
- [ ] **Non-root user** - Security best practice
- [ ] **Multi-stage build** - Reduce final image size
- [ ] **Dev compose file** - Hot reload for development
- [ ] **Production compose** - Optimized for deployment
- [ ] **Init script** - Run RAG initialization on first start
- [ ] **Logging** - Configure container logging drivers

#### Docker Commands Reference
```bash
# Build the image
docker build -t ai-finance-assistant .

# Run with environment variables
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  ai-finance-assistant

# Using docker-compose
docker-compose up -d

# View logs
docker-compose logs -f app

# Rebuild after changes
docker-compose up -d --build

# Initialize RAG index in container
docker-compose exec app python scripts/init_rag.py

# Shell into container
docker-compose exec app bash
```

#### Image Optimization
- [ ] Use slim base image (python:3.11-slim)
- [ ] Multi-stage build to exclude build tools
- [ ] Minimize layers with combined RUN commands
- [ ] Use .dockerignore to reduce context size
- [ ] Target image size: < 1GB (ideally ~500MB)

### Security
- [ ] API key rotation
- [ ] Secrets management (Vault)
- [ ] HTTPS enforcement
- [ ] Input sanitization audit

---

## 10. Performance Optimization

### Latency
- [ ] Response streaming
- [ ] Async agent execution
- [ ] Connection pooling
- [ ] CDN for static assets

### Caching
- [ ] Redis caching layer
- [ ] LLM response caching (for common queries)
- [ ] Embedding cache warming
- [ ] **Short TTL caching (1 hour)** - Cache API responses with configurable TTL

#### Caching Implementation with TTL
```python
from functools import lru_cache
from cachetools import TTLCache
import time

# In-memory cache with 1 hour TTL
cache = TTLCache(maxsize=1000, ttl=3600)  # 1 hour = 3600 seconds

def cached_with_ttl(ttl_seconds: int = 3600):
    """Decorator for caching with TTL."""
    def decorator(func):
        cache = {}
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            if key in cache:
                result, timestamp = cache[key]
                if time.time() - timestamp < ttl_seconds:
                    return result
            result = func(*args, **kwargs)
            cache[key] = (result, time.time())
            return result
        return wrapper
    return decorator

# Usage
@cached_with_ttl(ttl_seconds=3600)  # 1 hour
def get_stock_price(ticker: str):
    return yf.Ticker(ticker).info

# Streamlit caching (built-in)
@st.cache_data(ttl=3600)  # 1 hour
def get_market_summary():
    return fetch_market_data()
```

### Cost
- [ ] Model selection based on query complexity
- [ ] Token usage optimization
- [ ] Batch processing for bulk operations

---

## 11. Pydantic Integration (Explore)

Evaluate adopting Pydantic more extensively for improved type safety, validation, and structured outputs.

### Structured LLM Outputs
- [ ] **Pydantic models for agent responses** - Define strict schemas for each agent's output
- [ ] **LangChain's `with_structured_output()`** - Force LLM to return Pydantic models
- [ ] **Validation on LLM responses** - Automatic retry on malformed outputs
- [ ] **Schema documentation** - Auto-generate API docs from Pydantic models

Example use cases:
```python
class PortfolioAnalysisOutput(BaseModel):
    """Structured output from Portfolio Agent."""
    total_value: float = Field(description="Total portfolio value in USD")
    allocation: Dict[str, float] = Field(description="Asset allocation percentages")
    risk_score: int = Field(ge=1, le=10, description="Risk score 1-10")
    recommendations: List[str] = Field(max_length=5)
    confidence: float = Field(ge=0, le=1)

class MarketDataOutput(BaseModel):
    """Structured market data response."""
    ticker: str
    price: float = Field(gt=0)
    change_pct: float
    volume: int = Field(ge=0)
    timestamp: datetime
```

### Input Validation
- [ ] **Query validation models** - Validate and sanitize user inputs
- [ ] **Portfolio upload validation** - Strict schema for CSV/JSON imports
- [ ] **Goal parameters validation** - Ensure sensible financial values
- [ ] **Configuration validation** - Type-safe config loading

### Benefits
| Benefit | Description |
|---------|-------------|
| Type Safety | Catch errors at runtime with clear messages |
| Self-documenting | Models serve as API documentation |
| Serialization | Easy JSON serialization/deserialization |
| IDE Support | Better autocomplete and type hints |
| LLM Integration | Native support in LangChain for structured outputs |

### Implementation Options
- [ ] **Pydantic v2** - Faster, better validation (already in requirements)
- [ ] **Instructor library** - Simplified structured outputs with retries
- [ ] **LangChain integration** - `llm.with_structured_output(PydanticModel)`
- [ ] **Guardrails AI** - Uses Pydantic for output validation

### Migration Path
1. Start with agent output models (highest value)
2. Add input validation for user-facing data
3. Replace TypedDict state with Pydantic models
4. Add structured output to LLM calls

### Considerations
- Performance overhead (minimal with Pydantic v2)
- Learning curve for team
- Migration effort for existing code
- Compatibility with LangGraph state (TypedDict vs Pydantic)

---

## 12. Agent Evaluation & Quality Metrics

Implement comprehensive evaluation for every agent response to ensure quality, accuracy, and safety.

### Evaluation Dimensions

| Dimension | Description | Weight | Method |
|-----------|-------------|--------|--------|
| **Accuracy** | Is the financial information factually correct? | High | LLM-as-Judge |
| **Relevance** | Does it answer the user's actual question? | High | LLM-as-Judge |
| **Faithfulness** | Is the response grounded in RAG context (no hallucination)? | High | RAGAS |
| **Completeness** | Does it cover all aspects of the question? | Medium | LLM-as-Judge |
| **Clarity** | Is it beginner-friendly and well-explained? | Medium | LLM-as-Judge |
| **Safety** | Includes disclaimers, avoids specific financial advice? | High | Rule-based |

---

### 12.1 LLM-as-a-Judge Evaluation Module

Use an LLM to evaluate response quality on a rubric. Fast, scalable, and works well for subjective quality metrics.

#### Core Implementation
```python
# src/evaluation/llm_judge.py
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage

class EvaluationResult(BaseModel):
    """Structured evaluation result."""
    accuracy: int = Field(ge=1, le=5, description="Factual correctness (1-5)")
    relevance: int = Field(ge=1, le=5, description="Answers the question (1-5)")
    completeness: int = Field(ge=1, le=5, description="Covers all aspects (1-5)")
    clarity: int = Field(ge=1, le=5, description="Beginner-friendly explanation (1-5)")
    overall_score: float = Field(ge=0, le=1, description="Weighted overall score")
    feedback: str = Field(description="Brief explanation of scores")
    flagged_issues: list[str] = Field(default_factory=list)

class LLMJudge:
    """Evaluate agent responses using LLM-as-a-Judge pattern."""

    EVALUATION_PROMPT = '''You are an expert evaluator for a financial education assistant.
Evaluate the following response on these criteria (1-5 scale):

1. ACCURACY: Is the financial information factually correct?
   - 5: Completely accurate, no errors
   - 3: Mostly accurate, minor issues
   - 1: Contains significant factual errors

2. RELEVANCE: Does the response address the user's question?
   - 5: Directly and fully answers the question
   - 3: Partially addresses the question
   - 1: Off-topic or misses the point

3. COMPLETENESS: Does it cover all important aspects?
   - 5: Comprehensive coverage
   - 3: Covers main points, misses some details
   - 1: Superficial or incomplete

4. CLARITY: Is it beginner-friendly and well-explained?
   - 5: Crystal clear, excellent for beginners
   - 3: Understandable but could be clearer
   - 1: Confusing or uses too much jargon

USER QUESTION: {query}

RESPONSE TO EVALUATE: {response}

CONTEXT USED (if any): {context}

Provide your evaluation in this exact format:
ACCURACY: [1-5]
RELEVANCE: [1-5]
COMPLETENESS: [1-5]
CLARITY: [1-5]
FEEDBACK: [Brief explanation]
ISSUES: [Comma-separated list of any concerns, or "None"]'''

    def __init__(self, llm=None):
        self.llm = llm or get_llm()  # Use cheaper model for evaluation

    def evaluate(
        self,
        query: str,
        response: str,
        context: Optional[str] = None
    ) -> EvaluationResult:
        """Evaluate a response and return structured scores."""
        prompt = self.EVALUATION_PROMPT.format(
            query=query,
            response=response,
            context=context or "No context provided"
        )

        result = self.llm.invoke([HumanMessage(content=prompt)])
        return self._parse_evaluation(result.content)

    def _parse_evaluation(self, raw_output: str) -> EvaluationResult:
        """Parse LLM output into structured result."""
        scores = {}
        feedback = ""
        issues = []

        for line in raw_output.strip().split('\n'):
            if line.startswith("ACCURACY:"):
                scores["accuracy"] = int(line.split(":")[1].strip())
            elif line.startswith("RELEVANCE:"):
                scores["relevance"] = int(line.split(":")[1].strip())
            elif line.startswith("COMPLETENESS:"):
                scores["completeness"] = int(line.split(":")[1].strip())
            elif line.startswith("CLARITY:"):
                scores["clarity"] = int(line.split(":")[1].strip())
            elif line.startswith("FEEDBACK:"):
                feedback = line.split(":", 1)[1].strip()
            elif line.startswith("ISSUES:"):
                issues_str = line.split(":", 1)[1].strip()
                if issues_str.lower() != "none":
                    issues = [i.strip() for i in issues_str.split(",")]

        # Calculate weighted overall score
        weights = {"accuracy": 0.3, "relevance": 0.3, "completeness": 0.2, "clarity": 0.2}
        overall = sum(scores.get(k, 3) * w for k, w in weights.items()) / 5

        return EvaluationResult(
            **scores,
            overall_score=overall,
            feedback=feedback,
            flagged_issues=issues
        )
```

#### Tasks
- [ ] **Create `src/evaluation/` module** - New package for evaluation components
- [ ] **Implement LLMJudge class** - Core evaluation logic with structured output
- [ ] **Add Pydantic models** - `EvaluationResult` for type-safe results
- [ ] **Support multiple rubrics** - Different criteria for different agent types
- [ ] **Use cheaper model** - GPT-3.5 or Claude Haiku for cost efficiency
- [ ] **Async evaluation** - Don't block response, evaluate in background
- [ ] **Evaluation caching** - Cache results for identical query/response pairs
- [ ] **Batch evaluation** - Evaluate multiple responses efficiently

---

### 12.2 RAGAS Framework Integration

Purpose-built metrics for RAG systems. Evaluates retrieval quality and response faithfulness.

#### Key Metrics

| Metric | What it Measures | Score Range |
|--------|------------------|-------------|
| **Faithfulness** | Is response supported by retrieved context? | 0-1 |
| **Answer Relevancy** | Does response address the query? | 0-1 |
| **Context Precision** | Are retrieved docs actually relevant? | 0-1 |
| **Context Recall** | Did we retrieve all needed info? | 0-1 |

#### Implementation
```python
# src/evaluation/ragas_eval.py
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from datasets import Dataset

class RAGASEvaluator:
    """Evaluate RAG pipeline using RAGAS metrics."""

    def __init__(self):
        self.metrics = [
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall
        ]

    def evaluate_response(
        self,
        query: str,
        response: str,
        contexts: list[str],
        ground_truth: Optional[str] = None
    ) -> Dict[str, float]:
        """Evaluate a single RAG response."""
        # Create dataset in RAGAS format
        data = {
            "question": [query],
            "answer": [response],
            "contexts": [contexts],
        }
        if ground_truth:
            data["ground_truth"] = [ground_truth]

        dataset = Dataset.from_dict(data)

        # Run evaluation
        result = evaluate(dataset, metrics=self.metrics)

        return {
            "faithfulness": result["faithfulness"],
            "answer_relevancy": result["answer_relevancy"],
            "context_precision": result["context_precision"],
            "context_recall": result.get("context_recall", None)
        }

    def evaluate_batch(self, samples: list[dict]) -> dict:
        """Evaluate multiple samples for aggregate metrics."""
        dataset = Dataset.from_dict({
            "question": [s["query"] for s in samples],
            "answer": [s["response"] for s in samples],
            "contexts": [s["contexts"] for s in samples],
        })

        result = evaluate(dataset, metrics=self.metrics)
        return result.to_pandas().mean().to_dict()
```

#### Faithfulness Check (Lightweight Alternative)
```python
# Simpler faithfulness check without full RAGAS
class FaithfulnessChecker:
    """Check if response is grounded in context."""

    PROMPT = '''Given the context and response below, identify any claims in the response
that are NOT supported by the context.

CONTEXT:
{context}

RESPONSE:
{response}

List unsupported claims (or say "None" if all claims are supported):'''

    def check(self, response: str, context: str) -> dict:
        result = self.llm.invoke(self.PROMPT.format(
            context=context,
            response=response
        ))

        unsupported = result.content.strip()
        is_faithful = unsupported.lower() == "none"

        return {
            "is_faithful": is_faithful,
            "unsupported_claims": [] if is_faithful else unsupported.split("\n"),
            "score": 1.0 if is_faithful else 0.5
        }
```

#### Tasks
- [ ] **Add RAGAS to requirements** - `ragas>=0.1.0`
- [ ] **Create RAGASEvaluator class** - Wrapper for RAGAS metrics
- [ ] **Implement faithfulness check** - Verify response is grounded in context
- [ ] **Add context quality metrics** - Evaluate retrieval before generation
- [ ] **Create golden dataset** - 50+ curated Q&A pairs for benchmarking
- [ ] **Batch evaluation script** - Evaluate entire knowledge base periodically
- [ ] **Track metrics over time** - Detect quality degradation

---

### 12.3 Rule-Based Safety Checks

Fast, deterministic checks for compliance and safety requirements.

#### Implementation
```python
# src/evaluation/safety_checks.py
from typing import Dict, List
import re

class SafetyChecker:
    """Rule-based safety and compliance checks."""

    # Patterns that indicate specific investment advice (should be avoided)
    ADVICE_PATTERNS = [
        r"you should (buy|sell|invest in)",
        r"I recommend (buying|selling|investing)",
        r"definitely (buy|sell|get)",
        r"guaranteed (return|profit|gain)",
        r"can't lose",
        r"sure thing",
    ]

    # Required disclaimer keywords
    DISCLAIMER_KEYWORDS = [
        "educational purposes",
        "not financial advice",
        "consult.*advisor",
        "do your own research",
    ]

    def check_response(self, response: str) -> Dict[str, Any]:
        """Run all safety checks on a response."""
        return {
            "has_disclaimer": self._check_disclaimer(response),
            "gives_specific_advice": self._check_specific_advice(response),
            "mentions_risk": self._check_risk_mention(response),
            "appropriate_tone": self._check_tone(response),
            "safety_score": self._calculate_safety_score(response),
            "issues": self._get_issues(response)
        }

    def _check_disclaimer(self, response: str) -> bool:
        """Check if response includes appropriate disclaimer."""
        response_lower = response.lower()
        return any(
            re.search(pattern, response_lower)
            for pattern in self.DISCLAIMER_KEYWORDS
        )

    def _check_specific_advice(self, response: str) -> bool:
        """Check if response gives specific investment advice."""
        response_lower = response.lower()
        return any(
            re.search(pattern, response_lower)
            for pattern in self.ADVICE_PATTERNS
        )

    def _check_risk_mention(self, response: str) -> bool:
        """Check if response appropriately mentions risks."""
        risk_terms = ["risk", "volatility", "loss", "decline", "downturn"]
        response_lower = response.lower()
        return any(term in response_lower for term in risk_terms)

    def _calculate_safety_score(self, response: str) -> float:
        """Calculate overall safety score (0-1)."""
        score = 1.0

        # Penalize for specific advice
        if self._check_specific_advice(response):
            score -= 0.4

        # Penalize for missing disclaimer
        if not self._check_disclaimer(response):
            score -= 0.2

        # Bonus for mentioning risks (in investment contexts)
        if self._check_risk_mention(response):
            score += 0.1

        return max(0, min(1, score))

    def _get_issues(self, response: str) -> List[str]:
        """Get list of safety issues found."""
        issues = []
        if self._check_specific_advice(response):
            issues.append("Contains specific investment advice")
        if not self._check_disclaimer(response):
            issues.append("Missing educational disclaimer")
        return issues
```

#### Tasks
- [ ] **Create SafetyChecker class** - Rule-based compliance checks
- [ ] **Define advice patterns** - Regex for detecting specific investment advice
- [ ] **Disclaimer enforcement** - Ensure every response has appropriate disclaimer
- [ ] **Risk mention tracking** - Check if risks are appropriately discussed
- [ ] **Configurable strictness** - Adjust thresholds for different use cases
- [ ] **Auto-remediation** - Automatically append disclaimer if missing

---

### 12.4 Evaluation Dashboard (UI)

Display quality metrics in the Streamlit interface for transparency and monitoring.

#### Dashboard Layout
```
┌─────────────────────────────────────────────────────────────────────┐
│  📊 Response Quality Metrics                                        │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │   4.2    │  │   4.5    │  │   4.0    │  │   4.8    │            │
│  │ Accuracy │  │Relevance │  │Complete  │  │ Clarity  │            │
│  │  ★★★★☆  │  │  ★★★★★  │  │  ★★★★☆  │  │  ★★★★★  │            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
├─────────────────────────────────────────────────────────────────────┤
│  RAG Quality                          │  Safety Checks              │
│  ┌─────────────────────────────────┐  │  ✅ Disclaimer present     │
│  │ Faithfulness    ████████░░ 82%  │  │  ✅ No specific advice     │
│  │ Context Prec.   ███████░░░ 75%  │  │  ✅ Appropriate tone       │
│  │ Answer Relevancy█████████░ 91%  │  │  ⚠️  Risk not mentioned    │
│  └─────────────────────────────────┘  │                             │
├─────────────────────────────────────────────────────────────────────┤
│  [▼ Evaluation Details]                                             │
│  Feedback: "Response accurately explains ETFs with clear examples.  │
│  Could improve by mentioning liquidity differences."                │
└─────────────────────────────────────────────────────────────────────┘
```

#### Implementation
```python
# In src/web_app/app.py - Add evaluation display

def render_evaluation_metrics(eval_result: dict):
    """Display evaluation metrics in an expander."""
    with st.expander("📊 Response Quality Metrics", expanded=False):
        # LLM Judge Scores
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            score = eval_result.get("accuracy", 0)
            st.metric("Accuracy", f"{score}/5", _score_delta(score))

        with col2:
            score = eval_result.get("relevance", 0)
            st.metric("Relevance", f"{score}/5", _score_delta(score))

        with col3:
            score = eval_result.get("completeness", 0)
            st.metric("Completeness", f"{score}/5", _score_delta(score))

        with col4:
            score = eval_result.get("clarity", 0)
            st.metric("Clarity", f"{score}/5", _score_delta(score))

        st.divider()

        # RAG Metrics
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**RAG Quality**")
            faithfulness = eval_result.get("faithfulness", 0)
            st.progress(faithfulness, text=f"Faithfulness: {faithfulness:.0%}")

            context_prec = eval_result.get("context_precision", 0)
            st.progress(context_prec, text=f"Context Precision: {context_prec:.0%}")

        with col2:
            st.markdown("**Safety Checks**")
            safety = eval_result.get("safety", {})
            if safety.get("has_disclaimer"):
                st.success("✅ Disclaimer present")
            else:
                st.warning("⚠️ Missing disclaimer")

            if not safety.get("gives_specific_advice"):
                st.success("✅ No specific advice")
            else:
                st.error("❌ Contains investment advice")

        # Feedback
        if eval_result.get("feedback"):
            st.info(f"💡 {eval_result['feedback']}")

def _score_delta(score: int) -> str:
    """Return delta indicator for score."""
    if score >= 4:
        return "Good"
    elif score >= 3:
        return "Fair"
    else:
        return "Needs improvement"


# Integration in chat response flow
def process_and_evaluate(query: str, **kwargs):
    """Process query and evaluate response."""
    # Get response from workflow
    result = process_query(query, **kwargs)

    # Run evaluation (async/background ideally)
    evaluator = get_evaluator()
    eval_result = evaluator.evaluate_full(
        query=query,
        response=result["response"],
        contexts=result.get("retrieved_context", [])
    )

    result["evaluation"] = eval_result
    return result
```

#### Tasks
- [ ] **Create evaluation display component** - Streamlit UI for metrics
- [ ] **Add to chat response** - Show eval metrics after each response
- [ ] **Collapsible by default** - Don't overwhelm casual users
- [ ] **Color-coded scores** - Visual indicators for quality levels
- [ ] **Historical tracking** - Store evaluations for trend analysis
- [ ] **Export functionality** - Download evaluation reports
- [ ] **Admin dashboard** - Aggregate metrics across all responses

---

### 12.5 Evaluation Storage & Analytics

Store evaluation results for analysis and improvement.

#### Storage Schema
```python
# src/evaluation/storage.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import json
from pathlib import Path

@dataclass
class EvaluationRecord:
    """Record of a single evaluation."""
    id: str
    timestamp: datetime
    session_id: str
    query: str
    response: str
    agents_used: list[str]

    # LLM Judge scores
    accuracy: int
    relevance: int
    completeness: int
    clarity: int

    # RAG metrics
    faithfulness: Optional[float]
    context_precision: Optional[float]

    # Safety
    safety_score: float
    safety_issues: list[str]

    # Overall
    overall_score: float
    feedback: str

class EvaluationStore:
    """Store and retrieve evaluation records."""

    def __init__(self, storage_path: str = "data/evaluations"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def save(self, record: EvaluationRecord):
        """Save evaluation record."""
        filename = f"{record.timestamp.strftime('%Y%m%d')}_{record.id}.json"
        filepath = self.storage_path / filename
        with open(filepath, 'w') as f:
            json.dump(record.__dict__, f, default=str)

    def get_analytics(self, days: int = 7) -> dict:
        """Get aggregate analytics for recent evaluations."""
        # Load recent records and compute averages
        pass

    def get_low_quality_responses(self, threshold: float = 0.6) -> list:
        """Get responses below quality threshold for review."""
        pass
```

#### Analytics Dashboard
```python
# Additional tab or section in UI
def render_analytics_dashboard():
    """Render evaluation analytics dashboard."""
    st.header("📈 Quality Analytics")

    store = EvaluationStore()
    analytics = store.get_analytics(days=7)

    # Overall quality trend
    st.subheader("Quality Trend (Last 7 Days)")
    st.line_chart(analytics["daily_scores"])

    # Score distribution
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Score Distribution")
        st.bar_chart(analytics["score_distribution"])

    with col2:
        st.subheader("Common Issues")
        for issue, count in analytics["top_issues"].items():
            st.write(f"- {issue}: {count}")

    # Low quality responses for review
    st.subheader("⚠️ Responses Needing Review")
    low_quality = store.get_low_quality_responses()
    for record in low_quality[:5]:
        with st.expander(f"Query: {record.query[:50]}..."):
            st.write(f"**Response:** {record.response[:200]}...")
            st.write(f"**Score:** {record.overall_score:.2f}")
            st.write(f"**Issues:** {', '.join(record.safety_issues)}")
```

#### Tasks
- [ ] **Create EvaluationStore class** - Persist evaluation records
- [ ] **JSON file storage** - Simple file-based storage initially
- [ ] **Analytics aggregation** - Compute averages, trends, distributions
- [ ] **Low-quality flagging** - Surface responses that need review
- [ ] **Admin dashboard page** - Dedicated analytics view
- [ ] **Export to CSV** - Download evaluation data for analysis
- [ ] **Database option** - SQLite or PostgreSQL for production

---

### Evaluation Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                        User Query                                   │
└─────────────────────────────┬───────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Agent Workflow                                   │
│              (Router → Agents → Synthesize)                         │
└─────────────────────────────┬───────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                Response + Metadata                                  │
│        (response, sources, agents_used, context)                    │
└─────────────────────────────┬───────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Evaluation Pipeline                               │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐       │
│  │   LLM Judge     │ │  RAGAS Metrics  │ │  Safety Checks  │       │
│  │ (Quality Scores)│ │  (RAG Quality)  │ │  (Compliance)   │       │
│  │                 │ │                 │ │                 │       │
│  │ • Accuracy      │ │ • Faithfulness  │ │ • Disclaimer    │       │
│  │ • Relevance     │ │ • Context Prec. │ │ • No advice     │       │
│  │ • Completeness  │ │ • Answer Rel.   │ │ • Risk mention  │       │
│  │ • Clarity       │ │ • Context Rec.  │ │ • Tone check    │       │
│  └────────┬────────┘ └────────┬────────┘ └────────┬────────┘       │
│           └──────────────┬────┴───────────────────┘                │
│                          ▼                                          │
│              ┌─────────────────────────┐                            │
│              │   Combined Evaluation   │                            │
│              │   • Overall Score       │                            │
│              │   • Feedback            │                            │
│              │   • Flagged Issues      │                            │
│              └───────────┬─────────────┘                            │
└──────────────────────────┼──────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Evaluation Store                                 │
│           (Persist for analytics & improvement)                     │
└─────────────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  UI Display & Dashboard                             │
│  • Per-response metrics (collapsible)                               │
│  • Analytics dashboard (admin)                                      │
│  • Low-quality alerts                                               │
└─────────────────────────────────────────────────────────────────────┘
```

### Requirements
```
# Add to requirements.txt
ragas>=0.1.0
```

### Priority for Evaluation Features

| Feature | Impact | Effort | Priority |
|---------|--------|--------|----------|
| LLM-as-Judge module | High | Medium | P1 |
| Safety rule checks | High | Low | P1 |
| Per-response UI display | High | Low | P1 |
| RAGAS integration | High | Medium | P1 |
| Evaluation storage | Medium | Low | P2 |
| Analytics dashboard | Medium | Medium | P2 |
| Batch evaluation script | Medium | Medium | P2 |
| Golden dataset creation | Medium | High | P2 |

---

## Priority Matrix

| Feature | Impact | Effort | Priority |
|---------|--------|--------|----------|
| Off-Topic Query Filter | High | Low | P0 |
| Output Guardrails | High | Medium | P0 |
| Financial Disclaimers | High | Low | P0 |
| Loading Quotes/Tips | Medium | Low | P0 |
| Loading Animation | Medium | Low | P0 |
| LangGraph Visualization | High | Low | P0 |
| Technical Summary Tab | High | Medium | P0 |
| RAG Citations Display | High | Low | P0 |
| Agent Execution Log | High | Low | P0 |
| Live Workflow Animation | High | High | P1 (Wow Factor) |
| Pydantic Structured Outputs | High | Medium | P1 |
| Hallucination Detection | High | High | P1 |
| Tax Planning Agent | Medium | High | P1 |
| Conversation Memory | Medium | Medium | P1 |
| LangGraph Checkpointer | High | Low | P1 |
| Portfolio Visualizations | High | Medium | P1 |
| Incremental Response Revision | Medium | High | P1 |
| Dockerization | High | Medium | P1 |
| HuggingFace Spaces Deploy | High | Medium | P1 |
| API Keys in UI | Medium | Low | P1 |
| Caching with TTL | Medium | Low | P1 |
| LLM-as-Judge Evaluation | High | Medium | P1 |
| RAGAS Integration | High | Medium | P1 |
| Evaluation Dashboard UI | High | Low | P1 |
| Safety Rule Checks | High | Low | P1 |
| LangSmith Tracing | Medium | Low | P2 |
| Response Streaming | Medium | Medium | P2 |
| Article Scraper | Medium | Medium | P2 |
| Brokerage CSV Import | Low | Medium | P3 |

---

## Demo Enhancement Ideas

For the capstone demo, consider showcasing:

1. **Guardrails in action**: Show how the system handles:
   - Off-topic queries ("What's a good recipe for pasta?")
   - Requests for specific investment advice
   - Attempts to bypass safety measures

2. **Multi-agent coordination**: Complex query that triggers multiple agents working together

3. **RAG accuracy**: Compare response with/without RAG context

4. **Error handling**: Graceful degradation when APIs are unavailable

5. **Loading experience**: Show rotating financial wisdom quotes/tips while LLM processes
   - Demonstrates attention to UX
   - Provides educational value even during wait times
   - Makes the app feel more polished and professional
   - Combine with animated spinner/progress indicator
   - Show multi-stage progress: "Routing..." → "Retrieving..." → "Generating..."

6. **Structured outputs with Pydantic**: Demonstrate type-safe, validated responses
   - Show how malformed LLM output is caught and retried
   - Display confidence scores and structured data
   - Highlight the reliability this adds to the system

7. **LangGraph visualization**: Show the workflow graph in action
   - Display the state graph diagram (Mermaid or interactive)
   - Highlight which nodes are executed for different query types
   - Show conditional routing decisions visually
   - Great for explaining the multi-agent architecture during demo

8. **Technical Summary Tab**: Dedicated section showcasing architecture
   - Project overview with tech stack badges
   - Architecture diagram (system overview)
   - LangGraph state graph with all nodes
   - Agent registry with descriptions
   - Knowledge base statistics
   - Perfect for interview demos - shows technical depth

9. **Live Workflow Animation** (Wow Factor): Real-time visualization during query processing
   - Nodes light up/pulse as they become active
   - Edges animate to show data flow direction
   - Timing breakdown shows duration per node
   - State inspection shows data at each step
   - Creates a "wow" moment during demos - interviewer sees the multi-agent system in action
   - Example flow: Router (green) → Finance QA (green, pulsing) → Synthesizer (green) → Done

10. **LangGraph Conversation Memory**: Show contextual follow-up questions
    - Ask "What are ETFs?" → Get answer
    - Follow up with "How do they compare to mutual funds?" → System remembers context
    - Then "Which is better for my portfolio?" → System recalls both ETF discussion AND portfolio
    - Demonstrates sophisticated state management and conversation continuity
    - Shows LangGraph checkpointer in action

11. **Agent Evaluation & Quality Metrics**: Showcase response quality assurance
    - Show evaluation scores (accuracy, relevance, clarity) after each response
    - Demonstrate faithfulness checking - response grounded in RAG context
    - Display safety compliance (disclaimer present, no specific advice)
    - Show RAG quality metrics (context precision, answer relevancy)
    - Perfect for demonstrating production-readiness and quality focus
    - Expand the "Quality Metrics" panel to show detailed evaluation breakdown

---

## Notes

- Tax agent requires careful legal review before implementation
- Guardrails should be configurable (strict/relaxed modes)
- Memory features need GDPR/privacy considerations
- Performance optimizations should be data-driven (profile first)
