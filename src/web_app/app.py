"""
Streamlit web application for AI Finance Assistant.
Provides a multi-tab interface for chat, portfolio analysis, market data, and goal planning.
"""

import sys
from pathlib import Path
from typing import Optional, List

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import uuid

# Import our modules
from src.workflow import process_query
from src.utils.market_data import (
    get_market_summary,
    get_stock_price,
    get_stock_info,
    get_historical_data,
    calculate_returns
)
from src.agents import PortfolioAnalysisAgent


# Page configuration
st.set_page_config(
    page_title="AI Finance Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    """Initialize session state variables."""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = None
    if 'goals' not in st.session_state:
        st.session_state.goals = []
    # Tab switching and pre-loading
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = 0  # Default to chat tab
    if 'switch_to_tab' not in st.session_state:
        st.session_state.switch_to_tab = None
    if 'preload_data' not in st.session_state:
        st.session_state.preload_data = {}
    if 'lookup_ticker' not in st.session_state:
        st.session_state.lookup_ticker = None


def main():
    """Main application entry point."""
    init_session_state()

    # Sidebar
    with st.sidebar:
        st.title("📈 AI Finance Assistant")
        st.markdown("---")
        st.markdown("""
        **Your AI-powered financial education companion**

        Learn about investing with personalized guidance:
        - 💬 Ask questions about finance
        - 📊 Analyze your portfolio
        - 📈 Check market data
        - 🎯 Plan your financial goals
        """)
        
        st.markdown("---")
        st.markdown("### 🚀 Smart Tab Navigation")
        st.markdown("""
        Ask questions and I'll guide you to the right tab!
        
        **Try these:**
        - "How is Apple doing?" → 📈 Market
        - "Analyze my portfolio" → 📊 Portfolio  
        - "Save $50K for a house" → 🎯 Goals
        """)

        st.markdown("---")
        st.markdown("### Quick Actions")

        if st.button("🔄 Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

        if st.button("📋 Load Sample Portfolio"):
            load_sample_portfolio()
            st.success("Sample portfolio loaded!")

    # Handle tab switching from agent response
    if st.session_state.switch_to_tab is not None:
        st.session_state.active_tab = st.session_state.switch_to_tab
        st.session_state.switch_to_tab = None
        # Force rerun to update tab selection
        st.rerun()

    # Custom tab selector for programmatic switching
    tab_names = ["💬 Chat", "📊 Portfolio", "📈 Market", "🎯 Goals"]
    
    # Use radio buttons styled as tabs (hidden label)
    selected_tab = st.radio(
        "Select Tab",
        options=range(len(tab_names)),
        format_func=lambda x: tab_names[x],
        index=st.session_state.active_tab,
        horizontal=True,
        label_visibility="collapsed",
        key="tab_selector"
    )
    
    # Update active tab when user manually switches
    if selected_tab != st.session_state.active_tab:
        st.session_state.active_tab = selected_tab
        st.rerun()

    # Render the selected tab
    st.markdown("---")
    
    if st.session_state.active_tab == 0:
        render_chat_tab()
    elif st.session_state.active_tab == 1:
        render_portfolio_tab()
    elif st.session_state.active_tab == 2:
        render_market_tab()
    elif st.session_state.active_tab == 3:
        render_goals_tab()


def render_chat_tab():
    """Render the chat interface tab."""
    st.header("💬 Financial Education Chat")
    st.markdown("Ask me anything about investing, financial planning, or your portfolio!")
    
    # Info about smart tab switching
    with st.expander("ℹ️ Smart Tab Switching"):
        st.markdown("""
        **Ask questions and I'll automatically take you to the relevant tab!**
        
        - 📈 **Market questions** (e.g., "How is Apple stock doing?") → Switches to Market tab
        - 📊 **Portfolio questions** → Switches to Portfolio tab  
        - 🎯 **Goal planning questions** → Switches to Goals tab
        
        The relevant tab will be pre-loaded with the information you asked about!
        """)

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask a financial question..."):
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = process_query(
                        query=prompt,
                        session_id=st.session_state.session_id,
                        portfolio=st.session_state.portfolio,
                        goals=st.session_state.goals
                    )
                    response = result.get("response", "I couldn't generate a response. Please try again.")

                    # Display response
                    st.markdown(response)

                    # Show agents used (for transparency)
                    agents_used = result.get("agents_used", [])
                    if agents_used:
                        st.caption(f"Agents used: {', '.join(agents_used)}")

                        # Handle automatic tab switching and data pre-loading
                        handle_agent_tab_switching(agents_used, prompt, result)

                    # Show sources in an expander (for RAG citations)
                    sources = result.get("sources", [])
                    if sources:
                        with st.expander("📚 Sources & References"):
                            for source in sources:
                                if isinstance(source, dict):
                                    title = source.get("title", source.get("source", "Unknown"))
                                    url = source.get("url")
                                    source_name = source.get("source", "")
                                    score = source.get("score", 0)

                                    if url:
                                        st.markdown(f"- [{title}]({url}) ({source_name}) - relevance: {score:.2f}")
                                    else:
                                        st.markdown(f"- {title} ({source_name}) - relevance: {score:.2f}")
                                else:
                                    st.markdown(f"- {source}")

                except Exception as e:
                    response = f"I encountered an error: {str(e)}. Please try again."
                    st.error(response)

        # Add assistant response to history
        st.session_state.chat_history.append({"role": "assistant", "content": response})

    # Example questions
    with st.expander("💡 Example Questions"):
        examples = [
            "What are RSUs and how are they taxed?",
            "Explain the difference between ETFs and mutual funds",
            "How should I think about diversification for my portfolio?",
            "What is dollar-cost averaging and why is it recommended?",
            "Can you explain compound interest with an example?",
            "What's the difference between a traditional and Roth IRA?",
        ]
        for example in examples:
            if st.button(example, key=f"ex_{example[:20]}"):
                st.session_state.chat_history.append({"role": "user", "content": example})
                st.rerun()


def render_portfolio_tab():
    """Render the portfolio analysis tab."""
    st.header("📊 Portfolio Analysis")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Upload Portfolio")
        st.markdown("""
        Upload a CSV file with your portfolio holdings.
        Required columns: `ticker`, `shares`
        Optional columns: `purchase_price`, `purchase_date`
        """)

        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.dataframe(df)

                if st.button("Analyze Portfolio"):
                    with st.spinner("Analyzing your portfolio..."):
                        # Parse portfolio
                        agent = PortfolioAnalysisAgent()
                        holdings = agent.parse_portfolio_csv(uploaded_file.getvalue().decode())

                        portfolio_data = {'holdings': holdings}
                        st.session_state.portfolio = portfolio_data

                        # Analyze
                        analysis = agent.analyze_portfolio(portfolio_data)

                        if 'error' not in analysis:
                            display_portfolio_analysis(analysis)
                        else:
                            st.error(f"Error: {analysis['error']}")

            except Exception as e:
                st.error(f"Error reading file: {str(e)}")

        st.markdown("---")
        st.subheader("Or Enter Manually")

        with st.form("manual_portfolio"):
            ticker = st.text_input("Ticker Symbol (e.g., AAPL)")
            shares = st.number_input("Number of Shares", min_value=0.0, step=1.0)
            price = st.number_input("Purchase Price (optional)", min_value=0.0, step=1.0)

            if st.form_submit_button("Add Holding"):
                if ticker and shares > 0:
                    if st.session_state.portfolio is None:
                        st.session_state.portfolio = {'holdings': []}

                    st.session_state.portfolio['holdings'].append({
                        'ticker': ticker.upper(),
                        'shares': shares,
                        'purchase_price': price if price > 0 else None
                    })
                    st.success(f"Added {shares} shares of {ticker.upper()}")
                    st.rerun()

    with col2:
        st.subheader("Current Portfolio")
        if st.session_state.portfolio and st.session_state.portfolio.get('holdings'):
            holdings_df = pd.DataFrame(st.session_state.portfolio['holdings'])
            st.dataframe(holdings_df)

            if st.button("Analyze Current Portfolio"):
                with st.spinner("Analyzing..."):
                    agent = PortfolioAnalysisAgent()
                    analysis = agent.analyze_portfolio(st.session_state.portfolio)
                    if 'error' not in analysis:
                        display_portfolio_analysis(analysis)
        else:
            st.info("No portfolio data yet. Upload a CSV or add holdings manually.")


def display_portfolio_analysis(analysis: dict):
    """Display portfolio analysis results."""
    st.markdown("---")
    st.subheader("Portfolio Analysis Results")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Value", f"${analysis['total_value']:,.2f}")
    with col2:
        st.metric("Total Gain/Loss",
                  f"${analysis['total_gain_loss']:,.2f}",
                  f"{analysis['total_gain_loss_pct']:.1f}%")
    with col3:
        st.metric("Holdings", analysis['num_holdings'])
    with col4:
        div_score = analysis['diversification_score']
        st.metric("Diversification", div_score['rating'], f"{div_score['score']}/100")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Sector Allocation")
        sector_data = analysis.get('sector_allocation', {})
        if sector_data:
            fig = px.pie(
                values=list(sector_data.values()),
                names=list(sector_data.keys()),
                title="Portfolio by Sector"
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Holdings Breakdown")
        holdings = analysis.get('holdings', [])
        if holdings:
            holdings_df = pd.DataFrame(holdings)
            fig = px.bar(
                holdings_df,
                x='ticker',
                y='current_value',
                title="Value by Holding",
                color='gain_loss_pct',
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig, use_container_width=True)

    # Holdings table
    st.subheader("Holdings Detail")
    if holdings:
        display_df = pd.DataFrame(holdings)[
            ['ticker', 'company_name', 'shares', 'current_price', 'current_value', 'gain_loss', 'gain_loss_pct', 'sector']
        ]
        display_df = display_df.rename(columns={
            'ticker': 'Ticker',
            'company_name': 'Company',
            'shares': 'Shares',
            'current_price': 'Price',
            'current_value': 'Value',
            'gain_loss': 'Gain/Loss',
            'gain_loss_pct': 'Gain %',
            'sector': 'Sector'
        })
        st.dataframe(display_df, use_container_width=True)


def render_market_tab():
    """Render the market overview tab."""
    st.header("📈 Market Overview")

    # Market summary
    st.subheader("Major Indices")
    with st.spinner("Loading market data..."):
        try:
            summary = get_market_summary()

            cols = st.columns(4)
            for i, (name, data) in enumerate(summary.items()):
                with cols[i]:
                    delta_color = "normal" if data['change'] >= 0 else "inverse"
                    st.metric(
                        name,
                        f"{data['price']:,.2f}",
                        f"{data['change_pct']:.2f}%",
                        delta_color=delta_color
                    )
        except Exception as e:
            st.error(f"Error loading market data: {str(e)}")

    st.markdown("---")

    # Stock lookup
    st.subheader("Stock Lookup")
    
    # Check if we have pre-loaded ticker data from chat
    preload_ticker = st.session_state.preload_data.get('ticker')
    if preload_ticker and preload_ticker != st.session_state.get('lookup_ticker'):
        st.session_state.lookup_ticker = preload_ticker
        # Clear preload data after using it
        st.session_state.preload_data = {}
        st.success(f"✨ Loaded {preload_ticker} from your question!")
    
    col1, col2 = st.columns([1, 2])

    with col1:
        default_ticker = st.session_state.get('lookup_ticker', 'AAPL')
        ticker = st.text_input("Enter Ticker Symbol", value=default_ticker)
        if st.button("Look Up"):
            st.session_state.lookup_ticker = ticker.upper()
            st.rerun()

    with col2:
        lookup_ticker = st.session_state.get('lookup_ticker', 'AAPL')
        if lookup_ticker:
            with st.spinner(f"Loading {lookup_ticker}..."):
                try:
                    price_data = get_stock_price(lookup_ticker)
                    info = get_stock_info(lookup_ticker)
                    returns = calculate_returns(lookup_ticker)

                    # Display info
                    st.subheader(f"{info.get('name', lookup_ticker)} ({lookup_ticker})")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Price", f"${price_data.get('price', 0):.2f}",
                                  f"{price_data.get('change_pct', 0):.2f}%")
                    with col2:
                        st.metric("P/E Ratio", f"{info.get('pe_ratio', 'N/A')}")
                    with col3:
                        div_yield = info.get('dividend_yield', 0) or 0
                        st.metric("Dividend Yield", f"{div_yield * 100:.2f}%")

                    # Returns
                    st.markdown("**Returns:**")
                    return_cols = st.columns(4)
                    for i, (period, ret) in enumerate(returns.items()):
                        with return_cols[i]:
                            st.metric(period, f"{ret}%" if ret else "N/A")

                    # Chart
                    hist = get_historical_data(lookup_ticker, period="6mo")
                    if not hist.empty:
                        fig = px.line(hist, y='Close', title=f"{lookup_ticker} - 6 Month Chart")
                        st.plotly_chart(fig, use_container_width=True)

                except Exception as e:
                    st.error(f"Error: {str(e)}")


def render_goals_tab():
    """Render the goal planning tab."""
    st.header("🎯 Financial Goal Planning")

    st.markdown("""
    Use this calculator to plan for your financial goals. We'll show you projections
    based on different return scenarios.
    """)
    
    # Check if we have pre-loaded goal amount from chat
    preload_amount = st.session_state.preload_data.get('target_amount')
    default_target = 100000
    if preload_amount:
        default_target = int(preload_amount)
        st.success(f"✨ Pre-filled target amount ${default_target:,} from your question!")
        # Clear preload data after showing message
        st.session_state.preload_data = {}

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Goal Parameters")

        goal_type = st.selectbox(
            "Goal Type",
            ["Retirement", "House Down Payment", "Education", "Emergency Fund", "Other"]
        )

        target_amount = st.number_input(
            "Target Amount ($)",
            min_value=0,
            value=default_target,
            step=10000,
            key="goal_target_amount"
        )

        current_savings = st.number_input(
            "Current Savings ($)",
            min_value=0,
            value=10000,
            step=1000
        )

        monthly_contribution = st.number_input(
            "Monthly Contribution ($)",
            min_value=0,
            value=500,
            step=100
        )

        years = st.slider(
            "Years Until Goal",
            min_value=1,
            max_value=40,
            value=10
        )

        risk_level = st.select_slider(
            "Risk Tolerance",
            options=["Conservative (4%)", "Moderate (6%)", "Aggressive (8%)"],
            value="Moderate (6%)"
        )

        calculate = st.button("Calculate Projection", type="primary")

    with col2:
        st.subheader("Projection Results")

        if calculate:
            # Parse risk level
            if "Conservative" in risk_level:
                rate = 0.04
            elif "Aggressive" in risk_level:
                rate = 0.08
            else:
                rate = 0.06

            # Calculate projections
            monthly_rate = rate / 12
            months = years * 12

            # Future value calculation
            if monthly_rate > 0:
                fv_current = current_savings * ((1 + monthly_rate) ** months)
                fv_contributions = monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate)
            else:
                fv_current = current_savings
                fv_contributions = monthly_contribution * months

            projected_total = fv_current + fv_contributions
            total_contributions = current_savings + (monthly_contribution * months)
            investment_growth = projected_total - total_contributions

            # Display results
            st.metric("Projected Total", f"${projected_total:,.0f}")

            if projected_total >= target_amount:
                surplus = projected_total - target_amount
                st.success(f"🎉 You'll exceed your goal by ${surplus:,.0f}!")
            else:
                shortfall = target_amount - projected_total
                st.warning(f"⚠️ You'll be ${shortfall:,.0f} short of your goal.")

                # Calculate required monthly
                remaining = target_amount - fv_current
                if monthly_rate > 0:
                    required_monthly = remaining * monthly_rate / (((1 + monthly_rate) ** months - 1))
                    st.info(f"💡 To reach your goal, contribute ${required_monthly:,.0f}/month")

            # Breakdown
            st.markdown("**Breakdown:**")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Contributions", f"${total_contributions:,.0f}")
            with col2:
                st.metric("Investment Growth", f"${investment_growth:,.0f}")

            # Projection chart
            st.subheader("Growth Over Time")
            years_list = list(range(years + 1))
            values = []
            for y in years_list:
                m = y * 12
                if monthly_rate > 0:
                    fv = current_savings * ((1 + monthly_rate) ** m) + \
                         monthly_contribution * (((1 + monthly_rate) ** m - 1) / monthly_rate)
                else:
                    fv = current_savings + monthly_contribution * m
                values.append(fv)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=years_list, y=values, mode='lines', name='Projected Value'))
            fig.add_hline(y=target_amount, line_dash="dash", line_color="red",
                          annotation_text="Target")
            fig.update_layout(
                title="Projected Growth",
                xaxis_title="Years",
                yaxis_title="Value ($)",
                yaxis_tickformat='$,.0f'
            )
            st.plotly_chart(fig, use_container_width=True)


def handle_agent_tab_switching(agents_used: List[str], query: str, result: dict):
    """
    Handle automatic tab switching based on which agent answered.
    Also extracts and pre-loads relevant data for the target tab.
    
    Args:
        agents_used: List of agent names that processed the query
        query: The original user query
        result: The complete result from process_query
    """
    # Mapping of agents to tab indices
    AGENT_TO_TAB = {
        'market_analysis': 2,      # Market tab
        'portfolio_analysis': 1,   # Portfolio tab
        'goal_planning': 3,        # Goals tab
        'news_synthesizer': 2,     # Market tab (news relates to market)
        'finance_qa': 0,           # Stay in chat tab
    }
    
    # Get the primary agent (first one used)
    if not agents_used:
        return
    
    primary_agent = agents_used[0]
    target_tab = AGENT_TO_TAB.get(primary_agent)
    
    # Only switch if not already in that tab and if we should switch
    if target_tab is not None and target_tab != 0:  # Don't switch for finance_qa
        # Extract relevant data based on agent type
        preload_data = {}
        
        if primary_agent == 'market_analysis':
            # Extract ticker symbols from query
            ticker = extract_ticker_from_query(query)
            if ticker:
                preload_data['ticker'] = ticker
                st.session_state.lookup_ticker = ticker
                # Show a helpful message with action button
                st.info(f"🚀 **Click the Market tab above** to see detailed {ticker} information with charts and metrics!")
        
        elif primary_agent == 'portfolio_analysis':
            # Pre-load portfolio analysis if we have portfolio data
            if st.session_state.portfolio:
                st.info("🚀 **Click the Portfolio tab above** for detailed analysis with charts and breakdowns!")
        
        elif primary_agent == 'goal_planning':
            # Extract goal-related numbers if present
            goal_amount = extract_dollar_amount(query)
            if goal_amount:
                preload_data['target_amount'] = goal_amount
                st.info(f"🚀 **Click the Goals tab above** to visualize your ${goal_amount:,.0f} goal with projections!")
            else:
                st.info("🚀 **Click the Goals tab above** to plan and visualize your financial goals!")
        
        # Store preload data and trigger tab switch
        st.session_state.preload_data = preload_data
        st.session_state.switch_to_tab = target_tab
        # Force immediate rerun to switch tabs
        st.rerun()


def extract_ticker_from_query(query: str) -> Optional[str]:
    """
    Extract ticker symbol from user query.
    
    Args:
        query: User's question
    
    Returns:
        Ticker symbol if found, None otherwise
    """
    import re
    
    # Common patterns for ticker symbols
    query_upper = query.upper()
    
    # Look for $ followed by ticker (e.g., $AAPL)
    dollar_match = re.search(r'\$([A-Z]{1,5})\b', query_upper)
    if dollar_match:
        return dollar_match.group(1)
    
    # Common stock tickers
    common_tickers = {
        'APPLE': 'AAPL',
        'MICROSOFT': 'MSFT',
        'GOOGLE': 'GOOGL',
        'ALPHABET': 'GOOGL',
        'AMAZON': 'AMZN',
        'TESLA': 'TSLA',
        'META': 'META',
        'FACEBOOK': 'META',
        'NVIDIA': 'NVDA',
        'AMD': 'AMD',
        'NETFLIX': 'NFLX',
        'DISNEY': 'DIS',
        'S&P 500': 'SPY',
        'S&P': 'SPY',
        'NASDAQ': 'QQQ',
    }
    
    for name, ticker in common_tickers.items():
        if name in query_upper:
            return ticker
    
    # Words to exclude (common financial terms that aren't tickers)
    excluded_terms = {
        'ETF', 'IRA', 'RSU', 'ESG', 'IPO', 'CEO', 'CFO', 'SEC',
        'STOCK', 'BOND', 'FUND', 'WHAT', 'HOW', 'WHY', 'WHO', 'WHEN',
        'IS', 'ARE', 'CAN', 'DOES', 'THE', 'AND', 'OR', 'FOR', 'WITH'
    }
    
    # Look for standalone 1-5 letter uppercase words (potential tickers)
    words = query_upper.split()
    for word in words:
        # Remove common punctuation
        clean_word = re.sub(r'[^A-Z]', '', word)
        if len(clean_word) >= 1 and len(clean_word) <= 5 and clean_word.isalpha():
            # Skip if it's an excluded term
            if clean_word in excluded_terms:
                continue
            # Check if it looks like a ticker (all caps in original)
            if clean_word in query:
                return clean_word
    
    return None


def extract_dollar_amount(query: str) -> Optional[float]:
    """
    Extract dollar amount from query.
    
    Args:
        query: User's question
    
    Returns:
        Dollar amount if found, None otherwise
    """
    import re
    
    # Look for patterns like $100,000 or $1M or 100k
    patterns = [
        r'\$([0-9,]+\.?[0-9]*)\s*(?:million|M)',  # $1.5M, $1 million
        r'\$([0-9,]+\.?[0-9]*)\s*(?:thousand|K)',  # $100K, $100 thousand
        r'\$([0-9,]+\.?[0-9]*)',  # $100,000
        r'([0-9,]+\.?[0-9]*)\s*(?:million|M)',  # 1.5M
        r'([0-9,]+\.?[0-9]*)\s*(?:thousand|K)',  # 100K
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                amount = float(amount_str)
                # Apply multipliers
                if re.search(r'million|M', match.group(0), re.IGNORECASE):
                    amount *= 1_000_000
                elif re.search(r'thousand|K', match.group(0), re.IGNORECASE):
                    amount *= 1_000
                return amount
            except ValueError:
                continue
    
    return None


def load_sample_portfolio():
    """Load a sample portfolio for demonstration."""
    st.session_state.portfolio = {
        'holdings': [
            {'ticker': 'VTI', 'shares': 50, 'purchase_price': 200},
            {'ticker': 'VXUS', 'shares': 30, 'purchase_price': 55},
            {'ticker': 'BND', 'shares': 40, 'purchase_price': 75},
            {'ticker': 'AAPL', 'shares': 10, 'purchase_price': 150},
            {'ticker': 'MSFT', 'shares': 8, 'purchase_price': 280},
        ]
    }


if __name__ == "__main__":
    main()
