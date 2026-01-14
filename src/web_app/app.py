"""
Streamlit web application for AI Finance Assistant.
Provides a multi-tab interface for chat, portfolio analysis, market data, and goal planning.
"""

import sys
from pathlib import Path

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
        st.markdown("### Quick Actions")

        if st.button("🔄 Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

        if st.button("📋 Load Sample Portfolio"):
            load_sample_portfolio()
            st.success("Sample portfolio loaded!")

    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "💬 Chat",
        "📊 Portfolio",
        "📈 Market",
        "🎯 Goals"
    ])

    with tab1:
        render_chat_tab()

    with tab2:
        render_portfolio_tab()

    with tab3:
        render_market_tab()

    with tab4:
        render_goals_tab()


def render_chat_tab():
    """Render the chat interface tab."""
    st.header("💬 Financial Education Chat")
    st.markdown("Ask me anything about investing, financial planning, or your portfolio!")

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
    col1, col2 = st.columns([1, 2])

    with col1:
        ticker = st.text_input("Enter Ticker Symbol", value="AAPL")
        if st.button("Look Up"):
            st.session_state.lookup_ticker = ticker.upper()

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
            value=100000,
            step=10000
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
