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
    calculate_returns,
    get_stock_news
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
    if 'pending_tab_action' not in st.session_state:
        st.session_state.pending_tab_action = None
    if 'navigate_to_tab' not in st.session_state:
        st.session_state.navigate_to_tab = None
    if 'selected_message_idx' not in st.session_state:
        st.session_state.selected_message_idx = None


def main():
    """Main application entry point."""
    init_session_state()

    # Global CSS for blue buttons - load this FIRST before any buttons render
    st.markdown("""
    <style>
    /* Nuclear option - override ALL primary button styles */
    button[kind="primary"],
    button[kind="primary"][data-testid="stFormSubmitButton"],
    button[kind="primary"][data-testid="baseButton-primary"],
    button.stButton,
    .stButton > button[kind="primary"],
    div[data-testid="stForm"] button,
    div[data-testid="stForm"] button[kind="primary"],
    form button[kind="primary"] {
        background: #0066cc !important;
        background-color: #0066cc !important;
        background-image: none !important;
        border: 1px solid #0066cc !important;
        color: white !important;
    }
    button[kind="primary"]:hover,
    button[kind="primary"][data-testid="stFormSubmitButton"]:hover,
    button[kind="primary"][data-testid="baseButton-primary"]:hover,
    .stButton > button[kind="primary"]:hover,
    div[data-testid="stForm"] button:hover,
    div[data-testid="stForm"] button[kind="primary"]:hover,
    form button[kind="primary"]:hover {
        background: #004c99 !important;
        background-color: #004c99 !important;
        background-image: none !important;
        border: 1px solid #004c99 !important;
        color: white !important;
    }
    button[kind="primary"]:active,
    button[kind="primary"][data-testid="stFormSubmitButton"]:active,
    button[kind="primary"][data-testid="baseButton-primary"]:active,
    .stButton > button[kind="primary"]:active,
    div[data-testid="stForm"] button:active,
    div[data-testid="stForm"] button[kind="primary"]:active,
    form button[kind="primary"]:active {
        background: #003d7a !important;
        background-color: #003d7a !important;
        background-image: none !important;
        border: 1px solid #003d7a !important;
        transform: scale(0.98);
    }
    </style>
    """, unsafe_allow_html=True)

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
        
        # Chat History in Sidebar
        st.markdown("---")
        if len(st.session_state.chat_history) > 0:
            with st.expander(f"📜 Chat History ({len(st.session_state.chat_history)} messages)", expanded=True):
                st.markdown("*Click a message to view full details*")
                
                # Group messages by pairs (user + assistant)
                for idx in range(0, len(st.session_state.chat_history), 2):
                    # Get user message
                    if idx < len(st.session_state.chat_history):
                        user_msg = st.session_state.chat_history[idx]
                        user_content = user_msg.get("content", "")
                        user_preview = user_content[:60] + "..." if len(user_content) > 60 else user_content
                        
                        # Check if there's an assistant response
                        has_response = (idx + 1) < len(st.session_state.chat_history)
                        
                        # Create clickable button for this message pair
                        button_label = f"💬 {user_preview}"
                        if st.button(
                            button_label,
                            key=f"msg_pair_{idx}",
                            use_container_width=True,
                            help="Click to view full conversation"
                        ):
                            st.session_state.selected_message_idx = idx
                            st.session_state.active_tab = 0  # Switch to chat tab
                            st.rerun()
                
                st.markdown("---")
                if st.button("🗑️ Clear All", key="sidebar_clear_history", use_container_width=True):
                    st.session_state.chat_history = []
                    st.session_state.selected_message_idx = None
                    st.rerun()
        
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

        if st.button("🔄 Start New Chat"):
            st.session_state.chat_history = []
            st.session_state.selected_message_idx = None
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

    # Check if user clicked the navigation button in chat
    # We do this BEFORE rendering tabs so navigation works
    if st.session_state.get('navigate_to_tab') is not None:
        st.session_state.active_tab = st.session_state.navigate_to_tab
        st.session_state.tab_selector = st.session_state.navigate_to_tab  # Also update the widget key
        st.session_state.navigate_to_tab = None
        st.session_state.pending_tab_action = None  # Clear the action

    # Initialize tab_selector if it doesn't exist
    if 'tab_selector' not in st.session_state:
        st.session_state.tab_selector = st.session_state.active_tab

    # Custom tab selector for programmatic switching
    tab_names = ["💬 Chat", "📊 Portfolio", "📈 Market", "🎯 Goals"]

    # Use pills (segmented control style) - more reliable than radio for programmatic switching
    def on_tab_change():
        """Callback when tab is manually changed."""
        st.session_state.active_tab = st.session_state.tab_selector
        st.session_state.pending_tab_action = None  # Clear pending action

    # Use radio with callback - the key links to session state
    st.radio(
        "Navigate:",
        options=range(len(tab_names)),
        format_func=lambda x: tab_names[x],
        horizontal=True,
        label_visibility="collapsed",
        key="tab_selector",
        on_change=on_tab_change
    )

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
        **Ask questions and I'll help you navigate to relevant details!**

        - 📈 **Market questions** (e.g., "How is Apple stock doing?") → Shows link to Market tab
        - 📊 **Portfolio questions** → Shows link to Portfolio tab
        - 🎯 **Goal planning questions** → Shows link to Goals tab

        The relevant tab will be pre-loaded with the information you asked about!
        """)

    # If a message is selected from sidebar, show it in detail
    if st.session_state.selected_message_idx is not None:
        idx = st.session_state.selected_message_idx
        
        st.markdown("---")
        st.markdown("### 📖 Viewing Selected Conversation")
        
        # Show the user question
        if idx < len(st.session_state.chat_history):
            user_msg = st.session_state.chat_history[idx]
            with st.chat_message("user"):
                st.markdown(user_msg.get("content", ""))
        
        # Show the assistant response if it exists
        if (idx + 1) < len(st.session_state.chat_history):
            assistant_msg = st.session_state.chat_history[idx + 1]
            with st.chat_message("assistant"):
                st.markdown(assistant_msg.get("content", ""))
                
                # Show metadata if available
                metadata = assistant_msg.get("metadata", {})
                if metadata:
                    agents = metadata.get("agents_used", [])
                    sources = metadata.get("sources", [])
                    
                    if agents:
                        st.caption(f"Agents used: {', '.join(agents)}")
                    
                    if sources:
                        with st.expander("📚 Sources & References"):
                            for source in sources:
                                if isinstance(source, dict):
                                    title = source.get("title", source.get("source", "Unknown"))
                                    url = source.get("url")
                                    st.markdown(f"- [{title}]({url})" if url else f"- {title}")
                                else:
                                    st.markdown(f"- {source}")
        
        # Button to go back to full chat
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("⬅️ Back to Full Chat", use_container_width=True):
                st.session_state.selected_message_idx = None
                st.rerun()
        
        st.markdown("---")
    
    else:
        # Normal chat view - show all messages
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Show pending action button AFTER chat history (so it appears below messages)
    if st.session_state.get('pending_tab_action'):
        action = st.session_state.pending_tab_action

        st.markdown("---")

        # Styled container for better visibility with accessible blue
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0066cc 0%, #004c99 100%);
                    padding: 20px;
                    border-radius: 10px;
                    margin: 10px 0;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.15);">
            <p style="color: white;
                      font-size: 17px;
                      font-weight: 600;
                      margin: 0;
                      text-align: center;">
                💡 {action['message']}
            </p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                f"{action['icon']} {action['button_text']} →",
                key="persistent_nav_button",
                type="primary",
                use_container_width=True
            ):
                # Set navigate_to_tab which will be checked at main level
                st.session_state.navigate_to_tab = action['tab_index']
                st.rerun()

        col_dismiss1, col_dismiss2, col_dismiss3 = st.columns([2, 1, 2])
        with col_dismiss2:
            if st.button("✕ Dismiss", key="dismiss_action", use_container_width=True):
                st.session_state.pending_tab_action = None
                st.rerun()

    # Chat input
    if prompt := st.chat_input("Ask a financial question..."):
        # Clear selected message when asking new question
        st.session_state.selected_message_idx = None
        
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
                    
                    # Collect metadata for this response
                    agents_used = result.get("agents_used", [])
                    sources = result.get("sources", [])
                    
                    # Add assistant response with metadata to history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response,
                        "metadata": {
                            "agents_used": agents_used,
                            "sources": sources
                        }
                    })

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

                    # Show clickable link to relevant tab - this will trigger rerun
                    if agents_used:
                        show_tab_navigation_link(agents_used, prompt, result)

                except Exception as e:
                    response = f"I encountered an error: {str(e)}. Please try again."
                    st.error(response)
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
    st.subheader("📊 Portfolio Analysis Results")

    # Add introduction
    st.markdown("""
    Here's a comprehensive breakdown of your portfolio's performance, diversification, and composition.
    Use these insights to understand your investment allocation and identify areas for optimization.
    """)

    # Summary metrics with explanations
    st.markdown("### 💰 Portfolio Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Value", f"${analysis['total_value']:,.2f}")
        st.caption("Current market value of all holdings")
    with col2:
        gain_loss = analysis['total_gain_loss']
        gain_loss_pct = analysis['total_gain_loss_pct']
        st.metric("Total Gain/Loss", f"${gain_loss:,.2f}", f"{gain_loss_pct:.1f}%")
        st.caption("Profit or loss since purchase")
    with col3:
        st.metric("Holdings", analysis['num_holdings'])
        st.caption("Number of different positions")
    with col4:
        div_score = analysis['diversification_score']
        st.metric("Diversification", div_score['rating'], f"{div_score['score']}/100")
        st.caption("How well your portfolio is spread across sectors")

    # Interpretation of overall performance
    if analysis['total_gain_loss_pct'] > 15:
        st.success("🎉 **Strong Performance!** Your portfolio has delivered excellent returns.")
    elif analysis['total_gain_loss_pct'] > 5:
        st.info("📈 **Solid Returns:** Your portfolio is performing well.")
    elif analysis['total_gain_loss_pct'] > 0:
        st.info("➡️ **Positive Territory:** Your portfolio is up, though modestly.")
    elif analysis['total_gain_loss_pct'] > -5:
        st.warning("📉 **Slight Loss:** Your portfolio is down slightly.")
    else:
        st.error("⚠️ **Significant Loss:** Consider reviewing your holdings.")

    # Charts with explanations
    st.markdown("### 📊 Visual Breakdown")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🥧 Sector Allocation")
        st.markdown("""
        This pie chart shows what percentage of your portfolio is invested in each sector.
        **Ideal:** A well-diversified portfolio typically has no more than 25-30% in any single sector.
        """)
        sector_data = analysis.get('sector_allocation', {})
        if sector_data:
            fig = px.pie(
                values=list(sector_data.values()),
                names=list(sector_data.keys()),
                title="Portfolio by Sector"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Add concentration warning
            max_sector = max(sector_data.values())
            if max_sector > 40:
                st.warning(f"⚠️ **High Concentration:** {max(sector_data, key=sector_data.get)} represents {max_sector:.1f}% of your portfolio. Consider diversifying.")
            elif max_sector > 30:
                st.info(f"ℹ️ {max(sector_data, key=sector_data.get)} is your largest sector at {max_sector:.1f}%.")

    with col2:
        st.markdown("#### 📊 Holdings by Value")
        st.markdown("""
        This bar chart shows the current value of each position, color-coded by performance:
        **Green** = gains, **Red** = losses.
        """)
        holdings = analysis.get('holdings', [])
        if holdings:
            holdings_df = pd.DataFrame(holdings)
            fig = px.bar(
                holdings_df,
                x='ticker',
                y='current_value',
                title="Value by Holding",
                color='gain_loss_pct',
                color_continuous_scale='RdYlGn',
                labels={'current_value': 'Current Value ($)', 'ticker': 'Ticker'}
            )
            st.plotly_chart(fig, use_container_width=True)

    # Holdings table with explanation
    st.markdown("### 📋 Detailed Holdings")
    st.markdown("""
    This table shows all your individual positions with current prices, values, and performance.
    Use this to identify your best and worst performers.
    """)

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

        # Add insights about best/worst performers
        best_performer = holdings_df.loc[holdings_df['gain_loss_pct'].idxmax()]
        worst_performer = holdings_df.loc[holdings_df['gain_loss_pct'].idxmin()]

        col1, col2 = st.columns(2)
        with col1:
            st.success(f"🏆 **Best Performer:** {best_performer['ticker']} (+{best_performer['gain_loss_pct']:.1f}%)")
        with col2:
            st.error(f"📉 **Worst Performer:** {worst_performer['ticker']} ({worst_performer['gain_loss_pct']:.1f}%)")


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

    # Ticker input using form (makes Enter key work)
    with st.form(key="ticker_lookup_form", clear_on_submit=False):
        col_input1, col_input2, col_input3 = st.columns([2, 1, 3])
        with col_input1:
            default_ticker = st.session_state.get('lookup_ticker', 'AAPL')
            ticker = st.text_input("Enter Ticker Symbol", value=default_ticker)
        with col_input2:
            # Add spacing to align button with input field
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("🔍 Look Up", type="primary", use_container_width=True)

        if submitted and ticker:
            st.session_state.lookup_ticker = ticker.upper()
            st.rerun()

    lookup_ticker = st.session_state.get('lookup_ticker', 'AAPL')
    if lookup_ticker:
        with st.spinner(f"Loading {lookup_ticker}..."):
            try:
                price_data = get_stock_price(lookup_ticker)
                info = get_stock_info(lookup_ticker)
                returns = calculate_returns(lookup_ticker)

                # Main layout: Left summary + Right charts
                col_left, col_right = st.columns([1, 2])

                with col_left:
                    # Company Performance Summary
                    st.markdown("### 📊 Performance Summary")
                    st.markdown(f"#### **{info.get('name', lookup_ticker)}**")
                    st.markdown(f"**Ticker:** {lookup_ticker}")

                    # Current price with large display
                    current_price = price_data.get('price', 0)
                    change_pct = price_data.get('change_pct', 0)
                    change_color = "🟢" if change_pct >= 0 else "🔴"
                    st.markdown(f"### {change_color} **${current_price:.2f}**")
                    if change_pct >= 0:
                        st.markdown(f"<span style='color: green; font-size: 18px;'>**+{change_pct:.2f}%** today</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span style='color: red; font-size: 18px;'>**{change_pct:.2f}%** today</span>", unsafe_allow_html=True)

                    st.markdown("---")

                    # Key metrics with bold highlights
                    st.markdown("#### 📈 **Key Metrics**")

                    pe_ratio = info.get('pe_ratio', 'N/A')
                    if pe_ratio != 'N/A':
                        st.markdown(f"**P/E Ratio:** {pe_ratio}")
                        if isinstance(pe_ratio, (int, float)) and pe_ratio < 15:
                            st.caption("✨ *Potentially undervalued*")
                        elif isinstance(pe_ratio, (int, float)) and pe_ratio > 30:
                            st.caption("⚠️ *High valuation*")

                    div_yield = info.get('dividend_yield', 0) or 0
                    st.markdown(f"**Dividend Yield:** {div_yield * 100:.2f}%")
                    if div_yield > 0.03:
                        st.caption("💰 *Good income stock*")

                    market_cap = info.get('market_cap', 0)
                    if market_cap:
                        if market_cap >= 1e12:
                            st.markdown(f"**Market Cap:** ${market_cap/1e12:.2f}T")
                        elif market_cap >= 1e9:
                            st.markdown(f"**Market Cap:** ${market_cap/1e9:.2f}B")
                        else:
                            st.markdown(f"**Market Cap:** ${market_cap/1e6:.2f}M")

                    st.markdown("---")

                    # Performance highlights
                    st.markdown("#### 🎯 **Performance Highlights**")

                    for period, ret in returns.items():
                        if ret and ret != "N/A":
                            ret_val = float(ret.strip('%')) if isinstance(ret, str) else ret
                            if ret_val > 0:
                                st.markdown(f"**{period}:** <span style='color: green;'>**+{ret}%**</span> ✅", unsafe_allow_html=True)
                            else:
                                st.markdown(f"**{period}:** <span style='color: red;'>**{ret}%**</span> 📉", unsafe_allow_html=True)

                    st.markdown("---")

                    # Quick interpretation
                    st.markdown("#### 💡 **Quick Take**")
                    
                    # Try multiple metrics to generate insights
                    quick_take_shown = False
                    
                    # Check 1 month performance
                    one_mo = returns.get('1mo')
                    if one_mo and one_mo != "N/A":
                        try:
                            mo_val = float(one_mo.strip('%')) if isinstance(one_mo, str) else one_mo
                            if mo_val > 15:
                                st.success("**🚀 Strong momentum** - Up significantly this month!")
                                quick_take_shown = True
                            elif mo_val > 5:
                                st.info("**📈 Positive trend** - Gaining this month")
                                quick_take_shown = True
                            elif mo_val < -15:
                                st.error("**📉 Sharp decline** - Down significantly this month")
                                quick_take_shown = True
                            elif mo_val < -5:
                                st.warning("**⚠️ Pullback** - Declining this month")
                                quick_take_shown = True
                        except:
                            pass
                    
                    # Check P/E ratio if no momentum signal
                    if not quick_take_shown and pe_ratio != 'N/A':
                        try:
                            pe_val = float(pe_ratio) if isinstance(pe_ratio, (int, float)) else None
                            if pe_val:
                                if pe_val < 15:
                                    st.success("**💎 Value opportunity** - Trading below average P/E")
                                    quick_take_shown = True
                                elif pe_val > 30:
                                    st.warning("**⚡ Premium valuation** - High P/E suggests growth expectations")
                                    quick_take_shown = True
                        except:
                            pass
                    
                    # Fallback to general assessment
                    if not quick_take_shown:
                        if div_yield > 0.03:
                            st.info("**💰 Income-focused** - Good dividend yield for income investors")
                        else:
                            st.info("**📊 Stable position** - Monitor for entry/exit opportunities")
                    
                    # Add a tip
                    st.caption("💡 *Tip: This is a quick snapshot. Do your own research before investing.*")

                    st.markdown("---")

                    # Top 3 News
                    st.markdown("#### 📰 **Latest News**")

                    news_items = get_stock_news(lookup_ticker, num_news=3)
                    
                    if news_items and len(news_items) > 0:
                        for news in news_items:
                            title = news.get('title', '')
                            link = news.get('link', '')
                            publisher = news.get('publisher', 'Financial News')
                            published = news.get('published', '')

                            if title and link:
                                # Format timestamp if available
                                time_str = ""
                                if published:
                                    try:
                                        from datetime import datetime
                                        pub_dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                                        time_str = pub_dt.strftime('%b %d, %Y')
                                    except:
                                        pass
                                
                                st.markdown(
                                    f"""
                                    <div style="margin-bottom: 12px; padding: 14px 16px; 
                                                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                                border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                                                transition: transform 0.2s;">
                                        <a href="{link}" target="_blank" rel="noopener noreferrer" 
                                           style="text-decoration: none; color: white; font-weight: 600; font-size: 15px; line-height: 1.4;">
                                            {title}
                                        </a>
                                        <div style="margin-top: 8px; display: flex; gap: 12px; align-items: center;">
                                            <span style="color: rgba(255,255,255,0.9); font-size: 12px; font-weight: 500;">
                                                📡 {publisher}
                                            </span>
                                            {f'<span style="color: rgba(255,255,255,0.7); font-size: 11px;">• {time_str}</span>' if time_str else ''}
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                    else:
                        st.info("No recent news available.")
                        st.markdown(
                            f"""
                            <div style="margin-bottom: 15px; padding: 10px; background-color: #f8f9fa; border-left: 3px solid #0066cc; border-radius: 4px;">
                                <a href="https://finance.yahoo.com/quote/{lookup_ticker}/news" target="_blank" rel="noopener noreferrer" 
                                   style="text-decoration: none; color: #0066cc; font-weight: 500; font-size: 14px;">
                                    📰 View Latest {lookup_ticker} News
                                </a>
                                <br>
                                <span style="color: #666; font-size: 12px; margin-top: 4px; display: inline-block;">
                                    🗞️ Yahoo Finance
                                </span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                with col_right:
                    # Display company name
                    st.markdown(f"### {info.get('name', lookup_ticker)} ({lookup_ticker})")

                    # Timeframe selector with tabs
                    st.markdown("#### 📉 Historical Price Chart")

                    # Bordered legend description box
                    st.markdown("""
                    <div style="border: 2px solid #000000;
                                border-radius: 8px;
                                padding: 15px;
                                background-color: #f8f9fa;
                                margin-bottom: 15px;">
                        <p style="margin: 0; font-size: 15px; font-weight: 600; color: #000000;">
                            📊 Chart Legend
                        </p>
                        <p style="margin: 8px 0 0 0; font-size: 14px; color: #333333;">
                            <span style="display: inline-block; width: 30px; height: 3px; background-color: #00CC66; vertical-align: middle; margin-right: 8px;"></span>
                            <strong>Solid Line:</strong> Daily closing stock price
                        </p>
                        <p style="margin: 8px 0 0 0; font-size: 14px; color: #333333;">
                            <span style="display: inline-block; width: 30px; height: 2px; border-top: 2px dashed #FFA500; vertical-align: middle; margin-right: 8px;"></span>
                            <strong>Dashed Line:</strong> 20-day moving average (smooths out daily fluctuations to show trend)
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    timeframe_tab1, timeframe_tab2, timeframe_tab3, timeframe_tab4, timeframe_tab5 = st.tabs([
                        "📅 1 Month", "📅 6 Months", "📅 YTD", "📅 1 Year", "📅 5 Years"
                    ])

                    # Helper function to create enhanced chart
                    def create_enhanced_chart(ticker, period, title_suffix):
                        try:
                            hist = get_historical_data(ticker, period=period)
                            if hist.empty:
                                st.warning(f"No data available for {period}")
                                return

                            # Calculate percentage change
                            first_price = hist['Close'].iloc[0]
                            last_price = hist['Close'].iloc[-1]
                            pct_change = ((last_price - first_price) / first_price) * 100

                            # Determine color based on performance
                            line_color = '#00CC66' if pct_change >= 0 else '#FF4444'
                            fill_color = 'rgba(0, 204, 102, 0.1)' if pct_change >= 0 else 'rgba(255, 68, 68, 0.1)'

                            # Create figure with candlestick-style enhancements
                            fig = go.Figure()

                            # Add filled area
                            fig.add_trace(go.Scatter(
                                x=hist.index,
                                y=hist['Close'],
                                fill='tozeroy',
                                fillcolor=fill_color,
                                line=dict(color=line_color, width=3),
                                name='Stock Price',
                                hovertemplate='<b>Date:</b> %{x|%Y-%m-%d}<br><b>Price:</b> $%{y:.2f}<extra></extra>'
                            ))

                            # Add 20-day moving average if enough data
                            if len(hist) >= 20:
                                ma20 = hist['Close'].rolling(window=20).mean()
                                fig.add_trace(go.Scatter(
                                    x=hist.index,
                                    y=ma20,
                                    line=dict(color='rgba(255, 165, 0, 0.8)', width=2, dash='dash'),
                                    name='20-Day Trend (Moving Average)',
                                    hovertemplate='<b>20-Day Trend:</b> $%{y:.2f}<extra></extra>'
                                ))

                            # Update layout for better visuals
                            fig.update_layout(
                                title=f"{ticker} - {title_suffix}",
                                title_font=dict(size=20, color='#1f77b4', family='Arial Black'),
                                hovermode='x unified',
                                plot_bgcolor='rgba(240, 240, 240, 0.5)',
                                paper_bgcolor='white',
                                xaxis=dict(
                                    title=dict(text="Date", font=dict(size=14, color='#000000')),
                                    showgrid=True,
                                    gridcolor='rgba(200, 200, 200, 0.3)',
                                    showline=True,
                                    linewidth=2,
                                    linecolor='gray',
                                    tickfont=dict(size=13, color='#000000')
                                ),
                                yaxis=dict(
                                    title=dict(text="Price ($)", font=dict(size=14, color='#000000')),
                                    showgrid=True,
                                    gridcolor='rgba(200, 200, 200, 0.3)',
                                    showline=True,
                                    linewidth=2,
                                    linecolor='gray',
                                    tickfont=dict(size=13, color='#000000')
                                ),
                                font=dict(size=12),
                                showlegend=True,
                                legend=dict(
                                    yanchor="top",
                                    y=0.99,
                                    xanchor="left",
                                    x=0.01,
                                    bgcolor="rgba(255, 255, 255, 0.8)"
                                )
                            )

                            st.plotly_chart(fig, use_container_width=True)

                            # Performance summary for this period
                            if pct_change > 10:
                                st.success(f"✅ **Strong performance:** Up {pct_change:.1f}% over {title_suffix.lower()}")
                            elif pct_change > 0:
                                st.info(f"📈 **Positive return:** Up {pct_change:.1f}% over {title_suffix.lower()}")
                            elif pct_change > -10:
                                st.warning(f"📉 **Slight decline:** Down {abs(pct_change):.1f}% over {title_suffix.lower()}")
                            else:
                                st.error(f"⚠️ **Significant drop:** Down {abs(pct_change):.1f}% over {title_suffix.lower()}")
                        except Exception as e:
                            st.error(f"Error creating chart: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())

                    with timeframe_tab1:
                        create_enhanced_chart(lookup_ticker, "1mo", "1 Month Performance")

                    with timeframe_tab2:
                        create_enhanced_chart(lookup_ticker, "6mo", "6 Month Performance")

                    with timeframe_tab3:
                        create_enhanced_chart(lookup_ticker, "ytd", "Year-to-Date Performance")

                    with timeframe_tab4:
                        create_enhanced_chart(lookup_ticker, "1y", "1 Year Performance")

                    with timeframe_tab5:
                        create_enhanced_chart(lookup_ticker, "5y", "5 Year Performance")

            except Exception as e:
                st.error(f"Error loading data for {lookup_ticker}: {str(e)}")


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
        st.subheader("📊 Projection Results")

        if calculate:
            st.markdown("""
            Based on your inputs, here's a realistic projection of how your savings will grow.
            This assumes consistent monthly contributions and average market returns.
            """)

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

            # Display results with context
            st.metric("Projected Total", f"${projected_total:,.0f}")
            st.caption(f"Your estimated savings after {years} years at {rate*100:.0f}% annual return")

            # Goal assessment with actionable feedback
            if projected_total >= target_amount:
                surplus = projected_total - target_amount
                st.success(f"🎉 **Excellent!** You'll exceed your ${target_amount:,.0f} goal by ${surplus:,.0f}")
                st.markdown(f"""
                **What this means:**
                - You're on track to reach your goal comfortably
                - You have a ${surplus:,.0f} cushion for unexpected expenses
                - Consider increasing your goal or reducing contributions
                """)
            else:
                shortfall = target_amount - projected_total
                shortfall_pct = (shortfall / target_amount) * 100
                st.warning(f"⚠️ **Shortfall Alert:** You'll be ${shortfall:,.0f} short ({shortfall_pct:.1f}% of goal)")

                st.markdown("**How to close the gap:**")
                # Calculate required monthly
                remaining = target_amount - fv_current
                if monthly_rate > 0:
                    required_monthly = remaining * monthly_rate / (((1 + monthly_rate) ** months - 1))
                    increase_needed = required_monthly - monthly_contribution
                    st.info(f"💡 **Option 1:** Increase monthly contribution to ${required_monthly:,.0f} (+${increase_needed:,.0f}/month)")

                # Option 2: Extend timeline
                st.info(f"💡 **Option 2:** Extend your timeline by {int(shortfall_pct/10)} more years")

                # Option 3: Higher returns
                st.info(f"💡 **Option 3:** Seek higher-return investments (consider more risk)")

            # Breakdown with explanation
            st.markdown("### 💸 Where Your Money Goes")
            st.markdown("This shows how much you'll contribute vs. how much comes from investment growth:")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Your Contributions", f"${total_contributions:,.0f}")
                st.caption("Money you'll save over time")
            with col2:
                st.metric("Investment Growth", f"${investment_growth:,.0f}")
                st.caption("Earnings from compound interest")

            growth_pct = (investment_growth / projected_total) * 100 if projected_total > 0 else 0
            if growth_pct > 40:
                st.success(f"🚀 **Power of Compounding:** {growth_pct:.0f}% of your final total comes from investment growth!")
            else:
                st.info(f"📈 Investment growth will contribute {growth_pct:.0f}% of your total.")

            # Projection chart with explanation
            st.markdown("### 📈 Visual Projection")
            st.markdown("""
            This chart shows how your savings will grow year by year. The blue line represents
            your projected balance, while the red dashed line shows your target.
            **Look for:** Where the blue line crosses the red line (that's when you reach your goal!)
            """)

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
            fig.add_trace(go.Scatter(
                x=years_list,
                y=values,
                mode='lines+markers',
                name='Projected Savings',
                line=dict(color='#1f77b4', width=3)
            ))
            fig.add_hline(
                y=target_amount,
                line_dash="dash",
                line_color="red",
                line_width=2,
                annotation_text="🎯 Target Goal",
                annotation_position="right"
            )
            fig.update_layout(
                title=f"Savings Growth Projection ({years} Years)",
                xaxis_title="Years from Now",
                yaxis_title="Total Savings ($)",
                yaxis_tickformat='$,.0f',
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Add milestone info
            milestone_year = None
            for i, val in enumerate(values):
                if val >= target_amount:
                    milestone_year = i
                    break

            if milestone_year:
                st.success(f"🎯 **Milestone:** You'll reach your goal in approximately **{milestone_year} years**!")
            else:
                st.warning(f"⏰ You won't quite reach your goal in {years} years. Adjust your inputs above to see how to get there.")


def show_tab_navigation_link(agents_used: List[str], query: str, result: dict):
    """
    Store a pending tab navigation action in session state.
    The button will be shown OUTSIDE the chat history to persist across reruns.

    Args:
        agents_used: List of agent names that processed the query
        query: The original user query
        result: The complete result from process_query
    """
    # Mapping of agents to tab indices and descriptions
    AGENT_TAB_INFO = {
        'market_analysis': {
            'tab_index': 2,
            'tab_name': '📈 Market',
            'icon': '📈'
        },
        'portfolio_analysis': {
            'tab_index': 1,
            'tab_name': '📊 Portfolio',
            'icon': '📊'
        },
        'goal_planning': {
            'tab_index': 3,
            'tab_name': '🎯 Goals',
            'icon': '🎯'
        },
        'news_synthesizer': {
            'tab_index': 2,
            'tab_name': '📈 Market',
            'icon': '📰'
        },
    }

    # Get the primary agent (first one used)
    if not agents_used:
        return

    primary_agent = agents_used[0]
    tab_info = AGENT_TAB_INFO.get(primary_agent)

    # Only show link if there's a relevant tab (not for general Q&A)
    if tab_info is None:
        return

    # Extract relevant data based on agent type
    preload_data = {}
    link_text = ""
    message_text = ""

    if primary_agent == 'market_analysis':
        ticker = extract_ticker_from_query(query)
        if ticker:
            preload_data['ticker'] = ticker
            link_text = f"View {ticker} details"
            message_text = f"Want to see detailed charts and metrics for {ticker}?"
        else:
            link_text = "View market analysis"
            message_text = "Want to explore detailed market data?"

    elif primary_agent == 'portfolio_analysis':
        if st.session_state.portfolio:
            link_text = "View portfolio breakdown"
            message_text = "Want to see detailed portfolio analysis with charts?"
        else:
            link_text = "Go to Portfolio tab"
            message_text = "Upload your portfolio to see detailed analysis"

    elif primary_agent == 'goal_planning':
        goal_amount = extract_dollar_amount(query)
        if goal_amount:
            preload_data['target_amount'] = goal_amount
            link_text = f"Visualize ${goal_amount:,.0f} goal"
            message_text = f"Want to see growth projections for your ${goal_amount:,.0f} goal?"
        else:
            link_text = "Plan your goal"
            message_text = "Want to visualize your financial goal with detailed projections?"

    # Store preload data
    st.session_state.preload_data = preload_data
    st.session_state.pending_tab_action = {
        'tab_index': tab_info['tab_index'],
        'icon': tab_info['icon'],
        'button_text': link_text,
        'message': message_text
    }

    # Force a rerun so the button appears immediately
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
    import json

    # Common patterns for ticker symbols
    query_upper = query.upper()

    # Look for $ followed by ticker (e.g., $AAPL)
    dollar_match = re.search(r'\$([A-Z]{1,5})\b', query_upper)
    if dollar_match:
        return dollar_match.group(1)

    # Load company tickers from JSON file
    ticker_file = Path(__file__).parent.parent / "data" / "company_tickers.json"
    try:
        with open(ticker_file, 'r') as f:
            common_tickers = json.load(f)
    except FileNotFoundError:
        # Fallback to minimal set if file not found
        common_tickers = {
            'APPLE': 'AAPL',
            'MICROSOFT': 'MSFT',
            'TESLA': 'TSLA',
            'WALMART': 'WMT',
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
