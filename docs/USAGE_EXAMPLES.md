# Smart Tab Switching - Usage Examples

## How It Works

The AI Finance Assistant now features **intelligent tab switching** that automatically guides you to the right place based on your questions. Here's what happens:

1. **Ask a question in Chat** - Type naturally, like you're talking to a human advisor
2. **Get an AI response** - The relevant agent answers your question
3. **See a helpful prompt** - You'll get a notification suggesting which tab to check
4. **Click the suggested tab** - The tab is pre-loaded with the information you asked about!

---

## Example Workflows

### 📈 Market Analysis Examples

#### Example 1: "How is Apple doing?"

**What you type in Chat:**
```
How is Apple stock doing today?
```

**What happens:**
1. ✅ Market Analysis agent provides current Apple stock info
2. 🔔 You see: "🚀 **Click the Market tab above** to see detailed AAPL information with charts and metrics!"
3. 📊 Click "Market" tab
4. ✨ AAPL is already loaded with:
   - Current price and day change
   - P/E ratio and dividend yield
   - Historical returns (1D, 1W, 1M, 6M)
   - 6-month price chart

**Try these variations:**
- "What's the price of $MSFT?"
- "Tell me about Tesla stock"
- "How's Microsoft doing?"
- "Show me GOOGL performance"
- "S&P 500 today"

---

#### Example 2: "Compare Amazon to its competitors"

**What you type:**
```
How is Amazon stock performing compared to the market?
```

**What happens:**
1. Agent discusses Amazon's performance
2. Market tab notification appears
3. Click Market tab → AMZN is pre-loaded
4. You can then manually look up competitors (WMT, TGT, etc.)

---

### 📊 Portfolio Analysis Examples

#### Example 3: "Analyze my portfolio"

**What you type:**
```
Can you analyze my portfolio diversification?
```

**What happens:**
1. ✅ Portfolio agent analyzes your holdings (if already uploaded)
2. 🔔 You see: "🚀 **Click the Portfolio tab above** for detailed analysis with charts and breakdowns!"
3. 📊 Click "Portfolio" tab
4. ✨ See:
   - Sector allocation pie chart
   - Holdings breakdown bar chart
   - Diversification score
   - Individual stock performance
   - Recommendations

**Note:** Make sure you've uploaded/entered portfolio data first!

---

### 🎯 Goal Planning Examples

#### Example 4: "Save $50,000 for a house"

**What you type in Chat:**
```
How can I save $50,000 for a house down payment in 5 years?
```

**What happens:**
1. ✅ Goal Planning agent provides savings strategy
2. 🔔 You see: "🚀 **Click the Goals tab above** to visualize your $50,000 goal with projections!"
3. 📊 Click "Goals" tab
4. ✨ Target amount field is pre-filled with $50,000
5. You can:
   - Adjust current savings
   - Set monthly contribution
   - Change time horizon to 5 years
   - Select risk tolerance
   - See if you'll reach your goal

**Try these variations:**
- "Save $1M for retirement"
- "Need $100K in 10 years"
- "Plan for $500,000 retirement"
- "How to save 2 million for retirement?"

---

#### Example 5: "Retirement planning"

**What you type:**
```
Help me plan for retirement
```

**What happens:**
1. Goal Planning agent discusses retirement strategies
2. Goals tab notification appears
3. Click Goals tab → Use calculator to model scenarios
4. Try different:
   - Target amounts ($500K, $1M, $2M)
   - Time horizons (10, 20, 30 years)
   - Risk levels (Conservative, Moderate, Aggressive)

---

### 💬 General Finance Q&A (Stays in Chat)

#### Example 6: "What is an ETF?"

**What you type:**
```
What is an ETF and how does it work?
```

**What happens:**
1. ✅ Finance QA agent provides educational answer
2. ❌ NO tab switching (you stay in Chat)
3. Answer uses RAG knowledge base
4. Sources shown in expandable section

**These questions stay in Chat:**
- "What are RSUs?"
- "Explain compound interest"
- "What's the difference between Roth and Traditional IRA?"
- "How does dollar-cost averaging work?"

---

## Command-Style Usage

You can use the chat like a **command interface**:

### Quick Commands

```
Look up TSLA
→ Market tab with Tesla data

Check NVDA
→ Market tab with Nvidia data

Analyze portfolio
→ Portfolio tab (if portfolio exists)

Plan for $100k
→ Goals tab with $100k pre-filled

Save 1M for retirement
→ Goals tab with $1M target
```

---

## Multi-Step Workflows

### Workflow 1: Complete Portfolio Review

1. **Upload portfolio** in Portfolio tab
2. **Ask in Chat:** "Analyze my portfolio"
3. **Click Portfolio tab** to see full analysis
4. **For any stock** you're curious about:
   - **Ask in Chat:** "How is [STOCK] doing?"
   - **Click Market tab** for details
5. **Set goals** based on analysis:
   - **Ask in Chat:** "Help me save $X"
   - **Click Goals tab** to plan

---

### Workflow 2: Research and Plan

1. **Ask in Chat:** "What's a good retirement savings goal?"
2. **Get educational answer** (stays in Chat)
3. **Ask in Chat:** "Plan for $1.5M retirement in 25 years"
4. **Click Goals tab** → $1.5M pre-filled
5. **Adjust parameters** and run projections
6. **For stock ideas:**
   - **Ask in Chat:** "What about index funds like SPY?"
   - **Click Market tab** to see SPY

---

## Tips for Best Results

### ✅ Do's

- **Be specific with tickers**: "How's AAPL?" is better than "How's that fruit company?"
- **Use clear amounts**: "$50K" or "$50,000" both work
- **Ask follow-up questions**: The chat remembers context
- **Switch tabs freely**: You can always come back to Chat

### ❌ Don'ts

- **Don't say "open Market tab"** - Just ask about stocks and it'll guide you
- **Don't clear chat unnecessarily** - You lose context
- **Don't worry about exact format** - Natural language works!

---

## Supported Ticker Recognition

The system recognizes:

### Direct Tickers
- AAPL, MSFT, TSLA, GOOGL, AMZN, etc.

### Company Names
- Apple → AAPL
- Microsoft → MSFT
- Tesla → TSLA
- Google / Alphabet → GOOGL
- Amazon → AMZN
- Meta / Facebook → META
- Nvidia → NVDA
- Netflix → NFLX
- Disney → DIS

### Indices
- S&P 500 / S&P → SPY
- NASDAQ → QQQ

### Dollar Notation
- $AAPL, $MSFT, etc.

---

## Amount Recognition

The system extracts:

- **Direct amounts**: $100,000
- **Abbreviated**: $100K, $50K
- **Millions**: $1M, $1.5M, $2 million
- **Without dollar sign**: 100K, 1M, 500000

---

## Troubleshooting

**Q: I asked about Apple but Market tab shows AAPL as "APL"**  
A: Try being more explicit: "Look up AAPL" or "Check $AAPL"

**Q: Goals tab didn't pre-fill my amount**  
A: Some formats might not be recognized. Just type it manually - still faster than calculating from scratch!

**Q: Portfolio tab shows error**  
A: Make sure you've uploaded or entered portfolio data first

**Q: Tab didn't switch automatically**  
A: Click the tab shown in the blue notification message. Streamlit limitations prevent true auto-switching.

---

## Advanced Usage

### Chaining Questions

```
You: "What's a good emergency fund size?"
AI: [Explains 3-6 months expenses]

You: "Help me save $20K for emergency fund"
AI: [Discusses strategy] + "Click Goals tab!"
→ Goals tab pre-filled with $20K
```

### Comparative Analysis

```
You: "How is Tesla doing?"
→ Market tab with TSLA

You: "Compare to Ford"
→ Chat answer, then manually look up F in Market tab
```

### Building a Portfolio

```
1. "Should I invest in AAPL?"
   → Research in Market tab

2. "What about diversification?"
   → Educational answer in Chat

3. Add stocks to Portfolio manually

4. "Analyze my portfolio"
   → See full analysis in Portfolio tab
```

---

## Summary

The smart tab switching feature **acts as your AI guide**, automatically:
- 🔍 **Detecting** what type of information you need
- 🎯 **Extracting** key data (tickers, amounts) from your questions  
- 📍 **Directing** you to the right tab
- ⚡ **Pre-loading** that data so it's ready instantly

**Result:** Less clicking, less typing, more insights! 🚀
