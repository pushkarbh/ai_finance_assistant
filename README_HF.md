---
title: AI Finance Assistant
emoji: 💰
colorFrom: green
colorTo: blue
sdk: streamlit
sdk_version: "1.31.0"
app_file: src/web_app/app.py
pinned: false
license: mit
---

# AI Finance Assistant

A multi-agent AI system for democratizing financial literacy through personalized education and analysis.

## 🌟 Features

- 🤖 **5 Specialized AI Agents**
  - Finance Q&A Agent (RAG-powered education)
  - Portfolio Analysis Agent (diversification & performance)
  - Market Analysis Agent (real-time data)
  - Goal Planning Agent (retirement & savings projections)
  - News Synthesizer Agent (market news summaries)

- 📚 **Knowledge Base**: 110 curated financial articles (1,973 chunks) in FAISS vector database
- 🛡️ **Production-Grade Safety**: 4-layer Guardrails AI validation (hybrid keyword + LLM)
- 📊 **Real-Time Market Data**: Live stock prices, news, and company information via yFinance
- 🎯 **Financial Goal Planning**: Multi-scenario projections (conservative, moderate, aggressive)
- ⚡ **Smart Caching**: 15-minute TTL for optimized performance
- 🔄 **Smart Tab Switching**: Contextual suggestions with data pre-population

## 🚀 Setup

This app requires an **OpenAI API key**. Configure it in the Space Settings:

1. Go to **Settings** → **Repository secrets**
2. Add the following secret:
   - **Name**: `OPENAI_API_KEY`
   - **Value**: Your OpenAI API key (starts with `sk-...`)

## 📖 Usage

### 💬 Chat Tab
Ask any financial question:
- "What is a Roth IRA?"
- "Explain compound interest"
- "How do 401(k)s work?"

### 📊 Portfolio Tab
1. Upload CSV file with columns: `ticker`, `shares`, `purchase_price`, `purchase_date`
2. Get real-time valuation, diversification score, and recommendations
3. See sector allocation and gain/loss tracking

### 📈 Market Analysis Tab
- Enter stock tickers (e.g., AAPL, MSFT, TSLA)
- Get current prices, volume, 52-week ranges, P/E ratios
- View recent financial news

### 🎯 Goals Tab
Set and track financial goals:
- Retirement planning
- House down payment
- Education funding
- Emergency fund
- General savings

## 🏗️ Architecture

**Multi-Agent Orchestration**: LangGraph StateGraph coordinates agent execution based on query type

**RAG Pipeline**: FAISS + sentence-transformers for semantic knowledge retrieval

**Safety Guardrails**: 4 custom validators (FinanceTopic, InappropriateContent, Scope, LLMRelevance)

**State Management**: Shared AgentState TypedDict enables seamless agent collaboration

## 📊 Example Queries

- "Analyze my portfolio and suggest retirement goals"
- "What's happening in the stock market today?"
- "I want to save $100,000 in 5 years. How much should I contribute monthly?"
- "Explain the difference between traditional and Roth IRAs"
- "How is Apple stock performing?"

## ⚠️ Disclaimer

**This application is for educational purposes only and does not constitute financial advice.** 

Always consult with qualified financial professionals before making investment decisions. The AI provides educational information based on general financial principles and should not be considered personalized financial advice.

## 🔧 Technology Stack

- **LangGraph**: Multi-agent workflow orchestration
- **LangChain**: LLM integration and RAG pipelines
- **Guardrails AI**: Production-ready validation framework
- **OpenAI GPT-4o-mini**: Cost-effective LLM
- **FAISS**: Vector similarity search
- **Streamlit**: Interactive web interface
- **yFinance**: Real-time market data

## 📄 License

MIT License - See LICENSE file for details

---

**Built with ❤️ to democratize financial literacy**
