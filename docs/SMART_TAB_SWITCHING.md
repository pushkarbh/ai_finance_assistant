# Smart Tab Switching & Environment Fixes

## Recent Issues Resolved (January 2026)

### 1. Venv Not Being Used
**Problem**: When running `streamlit run`, it was using the base conda Python instead of the venv.

**Solution**: Created `run_app.sh` script that:
- Activates the venv
- Runs Streamlit using `python -m streamlit` (ensures venv Python is used)
- Properly manages the environment

**Usage**:
```bash
./run_app.sh
```

### 2. StreamlitAPIException: set_page_config() Error
**Problem**: `st.set_page_config()` was being called after other Streamlit commands, causing:
```
StreamlitAPIException: set_page_config() can only be called once per app page, 
and must be called as the first Streamlit command in your script.
```

**Root Cause**: The `@st.cache_data` decorator in `graph.py` was being evaluated at import time (when `from src.workflow import process_query` was executed), which triggered Streamlit before `set_page_config()`.

**Solution**: 
1. Moved `st.set_page_config()` to be the FIRST command in app.py (before imports)
2. Refactored caching in `graph.py` to use lazy decorator application:
   - Removed direct `import streamlit` at module level
   - Created `_get_cached_process_query()` that applies the decorator at runtime
   - Falls back to non-cached execution if Streamlit isn't available

**Code Changes**:

**app.py**:
```python
import streamlit as st
# ... other imports

# Page configuration - MUST be first Streamlit command
st.set_page_config(...)

# Import our modules AFTER set_page_config
from src.workflow import process_query
```

**graph.py**:
```python
# Removed: import streamlit as st at top

def process_query(...):
    try:
        import streamlit as st
        return _get_cached_process_query()(...)
    except:
        # Fallback without caching
        workflow = get_workflow()
        return workflow.run(...)

def _get_cached_process_query():
    """Lazily apply cache decorator"""
    global _CACHED_FUNCTION
    if _CACHED_FUNCTION is None:
        import streamlit as st
        _CACHED_FUNCTION = st.cache_data(ttl=900)(...)
    return _CACHED_FUNCTION
```

## Running the App
Always use the run script to ensure proper environment:
```bash
./run_app.sh
```

Or manually:
```bash
source venv/bin/activate
python -m streamlit run src/web_app/app.py --server.port 8502
```

**Do NOT use** (will use wrong Python):
```bash
streamlit run src/web_app/app.py  # ❌ Uses conda Python
```

---

# Original Documentation: Smart Tab Switching Feature

## Overview

The AI Finance Assistant now features **intelligent tab navigation** that automatically guides you to the right place based on your questions. When you ask about stocks, portfolios, or financial goals, the system:

1. ✅ **Answers your question** with the appropriate specialized agent
2. 🎯 **Extracts key information** (ticker symbols, dollar amounts, etc.)
3. 💡 **Shows a helpful notification** telling you which tab to visit
4. ⚡ **Pre-loads the data** so when you click the tab, everything is ready

> **Note:** Due to Streamlit limitations, tabs don't auto-switch. Instead, you'll see a notification message telling you which tab to click. The target tab is pre-loaded with your data for instant access!

## Implementation Details

### Architecture

The feature consists of three main components:

1. **Agent Detection** - Tracks which agent(s) answered your query
2. **Data Extraction** - Pulls out tickers, amounts, and other parameters
3. **Tab Navigation** - Uses radio buttons styled as tabs for programmatic control

### How It Works

When you ask a question in the Chat tab:

1. Query is processed by LangGraph workflow
2. Appropriate agent(s) handle the question
3. `handle_agent_tab_switching()` function analyzes the result:
   - Maps agent to target tab
   - Extracts relevant data (ticker, amount, etc.)
   - Sets session state variables
   - Shows notification message
4. When you click the suggested tab:
   - Pre-loaded data is detected
   - UI auto-populates with that data
   - Success message confirms the data was loaded

## Examples

### Market Questions

**Ask:** "How is Apple stock doing?"

**What Happens:**
- Market Analysis agent answers with current Apple stock info
- Chat shows: "💡 Check out the **Market** tab for detailed AAPL information!"
- When you click the Market tab, AAPL is already loaded with full details

**Supported Ticker Formats:**
- Company names: "Apple", "Microsoft", "Tesla"
- Ticker symbols: "AAPL", "MSFT", "TSLA"
- Dollar signs: "$AAPL", "$GOOGL"
- Common indices: "S&P 500" → SPY, "NASDAQ" → QQQ

### Portfolio Questions

**Ask:** "Can you analyze my portfolio diversification?"

**What Happens:**
- Portfolio Analysis agent provides insights
- Chat shows: "💡 Check out the **Portfolio** tab for detailed analysis!"
- Portfolio tab is ready with full analysis charts and metrics

### Goal Planning Questions

**Ask:** "How can I save $100,000 for retirement?"

**What Happens:**
- Goal Planning agent provides savings strategy
- Chat shows: "💡 Check out the **Goals** tab to plan and visualize your financial goals!"
- Goals tab may pre-populate the target amount if extracted from your question

## Supported Agents → Tabs Mapping

| Agent | Target Tab | Example Questions |
|-------|-----------|-------------------|
| **market_analysis** | 📈 Market | "How is TSLA doing?", "What's the current price of Apple?", "How's the market today?" |
| **portfolio_analysis** | 📊 Portfolio | "Analyze my portfolio", "Is my portfolio diversified?", "Review my holdings" |
| **goal_planning** | 🎯 Goals | "Help me save for retirement", "How much do I need to retire?", "Financial goals" |
| **news_synthesizer** | 📈 Market | "Latest Tesla news", "What's happening in the markets?" |
| **finance_qa** | 💬 Chat | "What are RSUs?", "Explain compound interest", "What's an ETF?" |

## Technical Details

### Ticker Extraction

The system can identify ticker symbols from:
- Direct mentions: "AAPL", "MSFT", "GOOGL"
- Dollar notation: "$AAPL"
- Company names: "Apple" → AAPL, "Microsoft" → MSFT
- Common indices: "S&P 500" → SPY

**Supported Common Tickers:**
- AAPL (Apple)
- MSFT (Microsoft)
- GOOGL (Google/Alphabet)
- AMZN (Amazon)
- TSLA (Tesla)
- META (Meta/Facebook)
- NVDA (Nvidia)
- AMD (AMD)
- NFLX (Netflix)
- DIS (Disney)
- SPY (S&P 500)
- QQQ (NASDAQ)

### Dollar Amount Extraction

The system can extract goal amounts from patterns like:
- "$100,000"
- "$1M" or "$1 million"
- "$100K" or "$100 thousand"
- "1.5M", "100K" (without dollar sign)

## Session State Variables

The feature uses these Streamlit session state variables:

- `switch_to_tab`: Target tab index to switch to
- `preload_data`: Dictionary of data to pre-load in the target tab
- `lookup_ticker`: Specific ticker to display in Market tab
- `active_tab`: Currently active tab index

## Customization

To modify the agent-to-tab mapping, edit the `AGENT_TO_TAB` dictionary in `handle_agent_tab_switching()`:

```python
AGENT_TO_TAB = {
    'market_analysis': 2,      # Market tab
    'portfolio_analysis': 1,   # Portfolio tab
    'goal_planning': 3,        # Goals tab
    'news_synthesizer': 2,     # Market tab
    'finance_qa': 0,           # Chat tab
}
```

## Benefits

1. **Seamless Navigation**: No manual tab switching needed
2. **Contextual Information**: Relevant data is pre-loaded
3. **Better UX**: Users get both chat answers AND detailed visuals/charts
4. **Educational**: Users learn where to find different types of information
5. **Efficient**: Reduces clicks and improves workflow

## Future Enhancements

Potential improvements:
- Auto-extract multiple tickers for comparison
- Pre-fill goal calculator fields from extracted amounts
- Remember user preferences for auto-switching
- Add animation/highlighting when switching tabs
- Support more complex queries with multiple data points
