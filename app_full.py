"""
Streamlit web application for AI Finance Assistant.
Provides a multi-tab interface for chat, portfolio analysis, market data, and goal planning.
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import traceback

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import uuid
import time
import threading
from contextlib import contextmanager

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="AI Finance Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Lazy import flag - imports happen on first use to speed up initial load
_imports_loaded = False
_import_error = None

def lazy_import():
    """Lazy load heavy imports after app starts to pass health checks faster."""
    global _imports_loaded, _import_error, process_query, get_market_summary
    global get_stock_price, get_stock_info, get_historical_data, calculate_returns
    global get_stock_news, PortfolioAnalysisAgent, get_random_tip
    
    if _imports_loaded:
        return True
    
    if _import_error:
        st.error(f"❌ **Critical Import Error:**")
        st.code(str(_import_error))
        st.stop()
        return False
    
    try:
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
        from src.web_app.financial_tips import get_random_tip
        
        # Make them global so other functions can use them
        globals()['process_query'] = process_query
        globals()['get_market_summary'] = get_market_summary
        globals()['get_stock_price'] = get_stock_price
        globals()['get_stock_info'] = get_stock_info
        globals()['get_historical_data'] = get_historical_data
        globals()['calculate_returns'] = calculate_returns
        globals()['get_stock_news'] = get_stock_news
        globals()['PortfolioAnalysisAgent'] = PortfolioAnalysisAgent
        globals()['get_random_tip'] = get_random_tip
        
        _imports_loaded = True
        return True
    except Exception as e:
        _import_error = f"{str(e)}\n\n{traceback.format_exc()}"
        st.error(f"❌ **Critical Import Error:**")
        st.code(_import_error)
        st.stop()
        return False


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


@contextmanager
def smart_spinner():
    """
    Display a financial tip while processing with animated spinner.
    Use as: with smart_spinner():
    """
    # Get a random financial tip to display
    tip = get_random_tip()

    # Create a placeholder for the status box
    status_placeholder = st.empty()

    # Show status with tip - st.status has built-in spinner animation
    with status_placeholder.container():
        status = st.status("🤔 **Analyzing your question...**", expanded=True, state="running")
        status.write("**While you wait, here's a financial tip:**")
        status.info(tip)

    try:
        yield  # Execute the code block
    finally:
        # Remove the status box completely after processing
        status_placeholder.empty()


def escape_dollar_signs(text: str) -> str:
    """
    Escape dollar signs in text to prevent LaTeX math rendering in Streamlit.
    Streamlit markdown interprets $...$ as LaTeX math, which causes formatting issues.
    """
    if not text:
        return text
    # Replace single $ with \$ to escape it
    return text.replace('$', r'\$')


def parse_return(val):
    """Helper function to parse return values from strings or floats."""
    if val is None or val == 'N/A':
        return -999
    if isinstance(val, float):
        return val
    if isinstance(val, str):
        val = val.strip().replace('%', '')
        if val == 'N/A' or val == '':
            return -999
        try:
            return float(val)
        except:
            return -999
    return -999


@st.cache_data(ttl=1800)  # Cache for 30 minutes
def load_top_stocks_performance():
    """Load performance data for top stocks. Cached for 30 minutes."""
    top_stocks = {
        'AAPL': 'Apple',
        'MSFT': 'Microsoft', 
        'GOOGL': 'Google',
        'AMZN': 'Amazon',
        'NVDA': 'Nvidia',
        'TSLA': 'Tesla',
        'META': 'Meta',
        'JPM': 'JPMorgan'
    }
    
    performance_data = []
    for ticker, name in top_stocks.items():
        try:
            returns = calculate_returns(ticker)
            price_data = get_stock_price(ticker)
            
            performance_data.append({
                'Ticker': ticker,
                'Company': name,
                'Price': f"${price_data.get('price', 0):,.2f}",
                '1 Month': returns.get('1mo', 'N/A'),
                '6 Months': returns.get('6mo', 'N/A'),
                'YTD': returns.get('ytd', 'N/A'),
                '5 Years': returns.get('5y', 'N/A')
            })
        except:
            continue
    
    return pd.DataFrame(performance_data) if performance_data else None


@st.cache_data(ttl=1800)  # Cache for 30 minutes
def load_global_indices_performance():
    """Load performance data for global indices. Cached for 30 minutes."""
    world_indices = {
        '^GSPC': 'S&P 500 (US)',
        '^DJI': 'Dow Jones (US)',
        '^IXIC': 'Nasdaq (US)',
        '^FTSE': 'FTSE 100 (UK)',
        '^GDAXI': 'DAX (Germany)',
        '^N225': 'Nikkei 225 (Japan)',
        '^HSI': 'Hang Seng (HK)',
        '^BSESN': 'Sensex (India)'
    }
    
    indices_data = []
    for symbol, name in world_indices.items():
        try:
            returns = calculate_returns(symbol)
            price_data = get_stock_price(symbol)
            
            indices_data.append({
                'Index': name,
                'Level': f"{price_data.get('price', 0):,.2f}",
                '1 Month': returns.get('1mo', 'N/A'),
                '6 Months': returns.get('6mo', 'N/A'),
                'YTD': returns.get('ytd', 'N/A'),
                '5 Years': returns.get('5y', 'N/A')
            })
        except:
            continue
    
    return pd.DataFrame(indices_data) if indices_data else None


@st.cache_data(ttl=1800)  # Cache for 30 minutes
def load_sector_performance():
    """Load performance data for sectors/industries. Cached for 30 minutes."""
    sectors_industries = {
        '💰 Precious Metals': {
            'GLD': 'Gold',
            'SLV': 'Silver'
        },
        '🏦 Banking & Financial': {
            'XLF': 'Financial Sector ETF',
            'JPM': 'JPMorgan Chase',
            'BAC': 'Bank of America'
        },
        '⚡ Energy': {
            'XLE': 'Energy Sector ETF',
            'XOM': 'ExxonMobil',
            'CL=F': 'Crude Oil'
        },
        '💻 Technology': {
            'XLK': 'Tech Sector ETF',
            'QQQ': 'Nasdaq 100 ETF'
        },
        '🏥 Healthcare & Pharma': {
            'XLV': 'Healthcare Sector ETF',
            'JNJ': 'Johnson & Johnson',
            'PFE': 'Pfizer'
        },
        '🏗️ Infrastructure': {
            'XLI': 'Industrial Sector ETF',
            'CAT': 'Caterpillar',
            'DE': 'Deere & Co'
        },
        '₿ Cryptocurrency': {
            'BTC-USD': 'Bitcoin',
            'ETH-USD': 'Ethereum'
        }
    }
    
    all_sector_data = []
    for sector_name, assets in sectors_industries.items():
        for symbol, name in assets.items():
            try:
                returns = calculate_returns(symbol)
                price_data = get_stock_price(symbol)
                
                all_sector_data.append({
                    'Sector': sector_name,
                    'Asset': name,
                    'Symbol': symbol,
                    'Price': f"${price_data.get('price', 0):,.2f}",
                    '1mo': returns.get('1mo', 'N/A'),
                    '6mo': returns.get('6mo', 'N/A'),
                    'ytd': returns.get('ytd', 'N/A'),
                    '5y': returns.get('5y', 'N/A')
                })
            except:
                continue
    
    return (pd.DataFrame(all_sector_data), sectors_industries) if all_sector_data else (None, sectors_industries)


@st.cache_data(ttl=1800)  # Cache for 30 minutes
def load_economic_indicators():
    """Load key economic indicators. Cached for 30 minutes."""
    economic_data = []
    
    # 1. Inflation (using TIPS ETF as proxy)
    try:
        tip_data = get_stock_price('TIP')
        tip_returns = calculate_returns('TIP')
        tip_ytd = parse_return(tip_returns.get('ytd', 0))
        tip_1yr = parse_return(tip_returns.get('1y', 0))
        
        # Fallback: YTD → 1yr → current price only
        if tip_ytd != -999:
            perf_str = f"{tip_ytd:+.2f}% YTD"
            perf_val = tip_ytd
        elif tip_1yr != -999:
            perf_str = f"{tip_1yr:+.2f}% (1yr)"
            perf_val = tip_1yr
        else:
            perf_str = ""
            perf_val = 0
        
        status = '🟢 Low' if perf_val < 2 else '🟡 Moderate' if perf_val < 5 else '🔴 High'
        value_display = f"${tip_data.get('price', 0):.2f}"
        if perf_str:
            value_display += f" ({perf_str})"
        
        economic_data.append({
            'Indicator': '📈 Inflation Expectations (TIP ETF)',
            'Value': value_display,
            'Significance': 'TIPS performance reflects inflation expectations; Fed targets ~2% inflation',
            'Status': status
        })
    except:
        pass
    
    # 2. Treasury Yields
    try:
        tnx_data = get_stock_price('^TNX')
        economic_data.append({
            'Indicator': '📈 10-Year Treasury Yield',
            'Value': f"{tnx_data.get('price', 0):.2f}%",
            'Significance': 'Benchmark for interest rates; rising yields can pressure stocks',
            'Status': '🟢 Normal' if tnx_data.get('price', 0) < 5 else '🟡 Elevated'
        })
    except:
        pass
    
    # 3. VIX
    try:
        vix_data = get_stock_price('^VIX')
        vix_val = vix_data.get('price', 0)
        status = '🟢 Low' if vix_val < 15 else '🟡 Moderate' if vix_val < 25 else '🔴 High'
        economic_data.append({
            'Indicator': '😰 VIX (Volatility Index)',
            'Value': f"{vix_val:.2f}",
            'Significance': 'Market fear gauge; <15=calm, 15-25=normal, >25=fearful',
            'Status': status
        })
    except:
        pass
    
    # 4. US Dollar Index
    try:
        dxy_data = get_stock_price('DX-Y.NYB')
        dxy_returns = calculate_returns('DX-Y.NYB')
        ytd = parse_return(dxy_returns.get('ytd', 0))
        yr1 = parse_return(dxy_returns.get('1y', 0))
        
        # Fallback: YTD → 1yr → current price only
        if ytd != -999:
            perf_str = f"{ytd:+.1f}% YTD"
            perf_val = ytd
        elif yr1 != -999:
            perf_str = f"{yr1:+.1f}% (1yr)"
            perf_val = yr1
        else:
            perf_str = ""
            perf_val = 0
        
        status = '🟢 Strengthening' if perf_val > 0 else '🔴 Weakening' if perf_val < 0 else '🟡 Stable'
        value_display = f"{dxy_data.get('price', 0):.2f}"
        if perf_str:
            value_display += f" ({perf_str})"
        
        economic_data.append({
            'Indicator': '💵 US Dollar Index',
            'Value': value_display,
            'Significance': 'Dollar strength affects exports, imports, and inflation',
            'Status': status
        })
    except:
        pass
    
    # 5. Crude Oil
    try:
        oil_data = get_stock_price('CL=F')
        oil_returns = calculate_returns('CL=F')
        ytd = parse_return(oil_returns.get('ytd', 0))
        yr1 = parse_return(oil_returns.get('1y', 0))
        
        # Fallback: YTD → 1yr → current price only
        if ytd != -999:
            perf_str = f"{ytd:+.1f}% YTD"
            perf_val = ytd
        elif yr1 != -999:
            perf_str = f"{yr1:+.1f}% (1yr)"
            perf_val = yr1
        else:
            perf_str = ""
            perf_val = 0
        
        status = '🟢 Stable' if abs(perf_val) < 15 else '🟡 Volatile'
        value_display = f"${oil_data.get('price', 0):.2f}/barrel"
        if perf_str:
            value_display += f" ({perf_str})"
        
        economic_data.append({
            'Indicator': '🛢️ Crude Oil (WTI)',
            'Value': value_display,
            'Significance': 'Energy costs impact inflation and consumer spending',
            'Status': status
        })
    except:
        pass
    
    # 6. Gold
    try:
        gold_data = get_stock_price('GC=F')
        gold_returns = calculate_returns('GC=F')
        ytd = parse_return(gold_returns.get('ytd', 0))
        yr1 = parse_return(gold_returns.get('1y', 0))
        
        # Fallback: YTD → 1yr → current price only
        if ytd != -999:
            perf_str = f"{ytd:+.1f}% YTD"
            perf_val = ytd
        elif yr1 != -999:
            perf_str = f"{yr1:+.1f}% (1yr)"
            perf_val = yr1
        else:
            perf_str = ""
            perf_val = 0
        
        status = '🟢 Rising' if perf_val > 5 else '🔴 Falling' if perf_val < -5 else '🟡 Stable'
        value_display = f"${gold_data.get('price', 0):,.2f}/oz"
        if perf_str:
            value_display += f" ({perf_str})"
        
        economic_data.append({
            'Indicator': '🥇 Gold Price',
            'Value': value_display,
            'Significance': 'Safe haven asset; rises during uncertainty or inflation fears',
            'Status': status
        })
    except:
        pass
    
    # 7. Silver (commodity)
    try:
        silver_data = get_stock_price('SI=F')
        silver_returns = calculate_returns('SI=F')
        ytd = parse_return(silver_returns.get('ytd', 0))
        yr1 = parse_return(silver_returns.get('1y', 0))
        
        # Fallback: YTD → 1yr → current price only
        if ytd != -999:
            perf_str = f"{ytd:+.1f}% YTD"
            perf_val = ytd
        elif yr1 != -999:
            perf_str = f"{yr1:+.1f}% (1yr)"
            perf_val = yr1
        else:
            perf_str = ""
            perf_val = 0
        
        status = '🟢 Rising' if perf_val > 5 else '🔴 Falling' if perf_val < -5 else '🟡 Stable'
        value_display = f"${silver_data.get('price', 0):,.2f}/oz"
        if perf_str:
            value_display += f" ({perf_str})"
        
        economic_data.append({
            'Indicator': '🥈 Silver Price',
            'Value': value_display,
            'Significance': 'Industrial & precious metal; tracks economic activity and inflation',
            'Status': status
        })
    except:
        pass
    
    # 8. Natural Gas (commodity)
    try:
        ng_data = get_stock_price('NG=F')
        ng_returns = calculate_returns('NG=F')
        ytd = parse_return(ng_returns.get('ytd', 0))
        yr1 = parse_return(ng_returns.get('1y', 0))
        
        # Fallback: YTD → 1yr → current price only
        if ytd != -999:
            perf_str = f"{ytd:+.1f}% YTD"
            perf_val = ytd
        elif yr1 != -999:
            perf_str = f"{yr1:+.1f}% (1yr)"
            perf_val = yr1
        else:
            perf_str = ""
            perf_val = 0
        
        status = '🟢 Stable' if abs(perf_val) < 20 else '🟡 Volatile'
        value_display = f"${ng_data.get('price', 0):.2f}/MMBtu"
        if perf_str:
            value_display += f" ({perf_str})"
        
        economic_data.append({
            'Indicator': '🔥 Natural Gas',
            'Value': value_display,
            'Significance': 'Energy commodity; affects heating costs and electricity prices',
            'Status': status
        })
    except:
        pass
    
    return economic_data


@st.cache_data(ttl=1800)  # Cache for 30 minutes
def load_market_news():
    """Load latest market news. Cached for 30 minutes."""
    try:
        return get_stock_news('^GSPC')  # S&P 500 news
    except:
        return []


def format_agent_name(agent_id: str) -> str:
    """Convert agent ID to human-readable name."""
    agent_names = {
        'finance_qa': 'Finance Q&A',
        'market_analysis': 'Market Analysis',
        'portfolio_analysis': 'Portfolio Analysis',
        'goal_planning': 'Goal Planning',
        'query_analyzer': 'Query Analyzer',
        'tax_optimizer': 'Tax Optimizer',
        'investment_advisor': 'Investment Advisor'
    }
    return agent_names.get(agent_id, agent_id.replace('_', ' ').title())


def display_agents_capsules(agents: List[str]) -> None:
    """Display agent names as visual capsules."""
    if not agents:
        return

    # Convert agent IDs to readable names
    agent_names = [format_agent_name(agent) for agent in agents]

    # Create HTML capsules
    capsules_html = "".join([
        f'<span style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
        f'color: white; padding: 4px 12px; border-radius: 16px; font-size: 12px; font-weight: 500; '
        f'margin-right: 6px; margin-bottom: 4px;">{name}</span>'
        for name in agent_names
    ])

    # Use st.write with HTML
    html_content = f'<div style="margin-top: 8px; margin-bottom: 4px;"><span style="color: #666; font-size: 13px; margin-right: 8px;">Agents used:</span>{capsules_html}</div>'
    st.write(html_content, unsafe_allow_html=True)


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

                        # Truncate to first 5-6 words
                        words = user_content.split()
                        if len(words) > 6:
                            user_preview = " ".join(words[:6]) + "..."
                        else:
                            user_preview = user_content

                        # Check if there's an assistant response
                        has_response = (idx + 1) < len(st.session_state.chat_history)

                        # Create clickable button for this message pair
                        button_label = f"💬 {user_preview}"
                        if st.button(
                            button_label,
                            key=f"msg_pair_{idx}",
                            use_container_width=True,
                            help=user_content  # Show full text on hover
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
            st.session_state.navigate_to_tab = 0  # Switch to Chat tab
            st.rerun()

        if st.button("📋 Load Sample Portfolio"):
            load_sample_portfolio()
            st.session_state.navigate_to_tab = 1  # Switch to Portfolio tab
            st.success("Sample portfolio loaded!")
            st.rerun()

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
        st.session_state.navigate_to_tab = None
        st.session_state.pending_tab_action = None  # Clear the action

    # Custom tab selector for programmatic switching
    tab_names = ["💬 Chat", "📊 Portfolio", "📈 Market", "🎯 Goals"]

    # Use radio WITHOUT callback to avoid circular state issues
    # Just use index parameter to control selection
    selected_tab = st.radio(
        "Navigate:",
        options=range(len(tab_names)),
        format_func=lambda x: tab_names[x],
        horizontal=True,
        label_visibility="collapsed",
        index=st.session_state.active_tab
    )
    
    # Update active_tab if user manually changed selection
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
                st.markdown(escape_dollar_signs(assistant_msg.get("content", "")))
                
                # Show metadata if available
                metadata = assistant_msg.get("metadata", {})
                if metadata:
                    agents = metadata.get("agents_used", [])
                    sources = metadata.get("sources", [])

                    if agents:
                        display_agents_capsules(agents)

                    # Show educational disclaimer
                    st.caption("⚠️ *Disclaimer: This is educational information and not financial advice. Always consider your personal financial situation and consult with a professional if needed. You're doing great by seeking knowledge—keep it up!*")

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

                # Show metadata for assistant messages
                if message["role"] == "assistant":
                    metadata = message.get("metadata", {})
                    if metadata:
                        sources = metadata.get("sources", [])
                        agents = metadata.get("agents_used", [])

                        # Show sources
                        if sources:
                            st.markdown("")
                            st.markdown("**📚 Sources:**")
                            citation_links = []
                            seen_citations = set()

                            for idx, source in enumerate(sources, 1):
                                if isinstance(source, dict):
                                    title = source.get("title", "")
                                    url = source.get("url")
                                    citation_key = url if url else title

                                    if citation_key and citation_key not in seen_citations:
                                        seen_citations.add(citation_key)
                                        if url:
                                            citation_links.append(f"[{title}]({url})")
                                        else:
                                            citation_links.append(source.get("source", title or f"Source {idx}"))
                                else:
                                    source_str = str(source)
                                    if source_str not in seen_citations:
                                        seen_citations.add(source_str)
                                        citation_links.append(source_str)

                            if citation_links:
                                st.markdown(" • ".join(citation_links))

                        # Show agents used
                        if agents:
                            display_agents_capsules(agents)

                        # Show educational disclaimer
                        st.caption("⚠️ *Disclaimer: This is educational information and not financial advice. Always consider your personal financial situation and consult with a professional if needed. You're doing great by seeking knowledge—keep it up!*")

    # Show pending action button AFTER chat history (so it appears below messages)
    if st.session_state.get('pending_tab_action'):
        action = st.session_state.pending_tab_action

        st.markdown("")

        # Message on first line
        st.markdown(f"**💡 {action['message']}**")

        # Buttons on second line, left aligned with minimal gap
        col_button1, col_button2, col_spacer = st.columns([1.5, 1.5, 5], gap="small")

        with col_button1:
            if st.button(
                f"{action['icon']} {action['button_text']}",
                key="persistent_nav_button",
                type="primary",
                use_container_width=True
            ):
                # Set navigate_to_tab which will be checked at main level
                st.session_state.navigate_to_tab = action['tab_index']
                st.rerun()

        with col_button2:
            # Use custom HTML button to avoid CSS conflicts
            dismiss_clicked = st.button("✕ Dismiss", key="dismiss_action", use_container_width=True)

            # Apply yellow styling only to this specific button using unique key selector
            st.markdown("""
            <style>
            /* Target only the dismiss button by its specific key */
            button[kind="secondary"][key="dismiss_action"],
            div[data-testid="column"] > div > div > button:has-text("✕ Dismiss") {
                background: #fff3cd !important;
                background-color: #fff3cd !important;
                background-image: none !important;
                color: #856404 !important;
                border: 1px solid #ffeaa7 !important;
            }
            button[kind="secondary"][key="dismiss_action"]:hover,
            div[data-testid="column"] > div > div > button:has-text("✕ Dismiss"):hover {
                background: #ffeaa7 !important;
                background-color: #ffeaa7 !important;
                background-image: none !important;
                border: 1px solid #ffd93d !important;
            }
            </style>
            """, unsafe_allow_html=True)

            if dismiss_clicked:
                st.session_state.pending_tab_action = None
                st.rerun()

    # Check if there's an unprocessed user message (from example questions)
    if (st.session_state.chat_history and
        st.session_state.chat_history[-1]["role"] == "user" and
        not st.session_state.get('processing_message', False)):

        # Mark as processing to avoid duplicate processing
        st.session_state.processing_message = True

        last_user_message = st.session_state.chat_history[-1]["content"]

        # Generate response
        with st.chat_message("assistant"):
            with smart_spinner():
                try:
                    result = process_query(
                        query=last_user_message,
                        session_id=st.session_state.session_id,
                        portfolio=st.session_state.portfolio,
                        goals=st.session_state.goals
                    )
                    response = result.get("response", "I couldn't generate a response. Please try again.")

                    # Check if response was cached
                    cache_hit = result.get("_cache_hit", False)
                    response_time = result.get("_response_time", 0)
                    cache_stats = result.get("_cache_stats", {})
                    
                    # Show cache status indicator
                    if cache_hit:
                        st.caption(f"⚡ Cached response ({response_time*1000:.0f}ms) • Total cache hits: {cache_stats.get('hits', 0)}")
                    else:
                        st.caption(f"🔄 New response ({response_time:.1f}s) • Total cache misses: {cache_stats.get('misses', 0)}")

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
                    st.markdown(escape_dollar_signs(response))

                    # Show inline citations if sources exist
                    if sources:
                        st.markdown("")
                        st.markdown("**📚 Sources:**")
                        citation_links = []
                        seen_citations = set()  # Deduplicate citations

                        for idx, source in enumerate(sources, 1):
                            if isinstance(source, dict):
                                title = source.get("title", "")
                                source_name = source.get("source", title or f"Source {idx}")
                                url = source.get("url")

                                # Create unique key for this citation
                                citation_key = url if url else title

                                # Only add if not already seen
                                if citation_key and citation_key not in seen_citations:
                                    seen_citations.add(citation_key)
                                    if url:
                                        citation_links.append(f"[{title}]({url})")
                                    else:
                                        citation_links.append(source_name)
                            else:
                                source_str = str(source)
                                if source_str not in seen_citations:
                                    seen_citations.add(source_str)
                                    citation_links.append(source_str)

                        if citation_links:
                            st.markdown(" • ".join(citation_links))
                    else:
                        st.caption("💡 No sources retrieved for this response")

                    # Show agents used (for transparency)
                    if agents_used:
                        display_agents_capsules(agents_used)

                    # Show educational disclaimer
                    st.caption("⚠️ *Disclaimer: This is educational information and not financial advice. Always consider your personal financial situation and consult with a professional if needed. You're doing great by seeking knowledge—keep it up!*")

                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": "I encountered an error processing your request. Please try again.",
                        "metadata": {}
                    })

        # Clear processing flag (no rerun needed - let response stay displayed inline)
        st.session_state.processing_message = False

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
            with smart_spinner():
                try:
                    result = process_query(
                        query=prompt,
                        session_id=st.session_state.session_id,
                        portfolio=st.session_state.portfolio,
                        goals=st.session_state.goals
                    )
                    response = result.get("response", "I couldn't generate a response. Please try again.")
                    
                    # Check if response was cached
                    cache_hit = result.get("_cache_hit", False)
                    response_time = result.get("_response_time", 0)
                    cache_stats = result.get("_cache_stats", {})
                    
                    # Show cache status indicator
                    if cache_hit:
                        st.caption(f"⚡ Cached response ({response_time*1000:.0f}ms) • Total cache hits: {cache_stats.get('hits', 0)}")
                    else:
                        st.caption(f"🔄 New response ({response_time:.1f}s) • Total cache misses: {cache_stats.get('misses', 0)}")
                    
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
                    st.markdown(escape_dollar_signs(response))

                    # Show inline citations if sources exist
                    sources = result.get("sources", [])

                    if sources:
                        st.markdown("")
                        st.markdown("**📚 Sources:**")
                        citation_links = []
                        seen_citations = set()  # Deduplicate citations

                        for idx, source in enumerate(sources, 1):
                            if isinstance(source, dict):
                                title = source.get("title", "")
                                source_name = source.get("source", title or f"Source {idx}")
                                url = source.get("url")

                                # Create unique key for this citation
                                citation_key = url if url else title

                                # Only add if not already seen
                                if citation_key and citation_key not in seen_citations:
                                    seen_citations.add(citation_key)
                                    if url:
                                        citation_links.append(f"[{title}]({url})")
                                    else:
                                        citation_links.append(source_name)
                            else:
                                source_str = str(source)
                                if source_str not in seen_citations:
                                    seen_citations.add(source_str)
                                    citation_links.append(source_str)

                        if citation_links:
                            st.markdown(" • ".join(citation_links))
                    else:
                        st.caption("💡 No sources retrieved for this response")

                    # Show agents used (for transparency)
                    agents_used = result.get("agents_used", [])
                    if agents_used:
                        display_agents_capsules(agents_used)

                    # Show educational disclaimer
                    st.caption("⚠️ *Disclaimer: This is educational information and not financial advice. Always consider your personal financial situation and consult with a professional if needed. You're doing great by seeking knowledge—keep it up!*")

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
            "Help me plan for retirement with $500K in 20 years",
            "I want to save $100K for a house down payment in 5 years",
            "How much should I contribute monthly to reach $1M by age 65?",
            "Should I max out my 401K or invest in a taxable account?",
            "Analyze my portfolio: 60% stocks, 30% bonds, 10% cash",
            "Is my portfolio too concentrated in tech stocks?",
            "How can I reduce risk in my retirement portfolio?",
            "What's a good asset allocation for someone in their 30s?",
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
                # Parse portfolio and store in session state
                agent = PortfolioAnalysisAgent()
                holdings = agent.parse_portfolio_csv(uploaded_file.getvalue().decode())
                portfolio_data = {'holdings': holdings}
                st.session_state.portfolio = portfolio_data
                st.success(f"✅ Portfolio loaded successfully with {len(holdings)} holdings")

            except Exception as e:
                st.error(f"Error reading file: {str(e)}")

        st.markdown("---")
        st.subheader("Or Enter Manually")

        # Investment type selector
        inv_type = st.radio(
            "Investment Type",
            ["Stock/ETF", "Bond", "Cash/Savings", "CD", "Other"],
            horizontal=True,
            key="manual_type"
        )

        if inv_type == "Stock/ETF":
            with st.form("manual_stock"):
                ticker = st.text_input("Ticker Symbol (e.g., AAPL)")
                shares = st.number_input("Number of Shares", min_value=0.0, step=1.0)
                price = st.number_input("Purchase Price (optional)", min_value=0.0, step=1.0)

                if st.form_submit_button("Add Stock"):
                    if ticker and shares > 0:
                        if st.session_state.portfolio is None:
                            st.session_state.portfolio = {'holdings': []}

                        new_holding = {
                            'type': 'stock',
                            'ticker': ticker.upper(),
                            'shares': shares
                        }
                        if price > 0:
                            new_holding['purchase_price'] = price

                        st.session_state.portfolio['holdings'].append(new_holding)
                        st.success(f"Added {shares} shares of {ticker.upper()}")
                        st.rerun()
        else:
            # Handle bonds, cash, CDs, other
            type_map = {
                "Bond": ("bond", "Bonds", "e.g., Treasury, Corporate, Municipal"),
                "Cash/Savings": ("cash", "Cash", "e.g., HYSA, Checking, Savings"),
                "CD": ("cd", "CD", "e.g., 1-year CD, 5-year CD"),
                "Other": ("other", "Other Investment", "e.g., Real Estate, Crypto")
            }

            inv_key, default_name, placeholder = type_map[inv_type]

            with st.form(f"manual_{inv_key}"):
                name = st.text_input(
                    "Investment Name/Description",
                    placeholder=placeholder
                )
                amount = st.number_input("Dollar Amount", min_value=0.0, step=100.0)
                rate = st.number_input(
                    "Interest Rate/Yield % (optional)",
                    min_value=0.0,
                    max_value=100.0,
                    step=0.1,
                    help="Annual yield or interest rate if applicable"
                )

                if st.form_submit_button(f"Add {inv_type}"):
                    if amount > 0:
                        if st.session_state.portfolio is None:
                            st.session_state.portfolio = {'holdings': []}

                        new_holding = {
                            'type': inv_key,
                            'name': name if name else default_name,
                            'shares': amount  # For non-stocks, shares = dollar amount
                        }
                        if rate > 0:
                            new_holding['purchase_price'] = rate  # Store rate as purchase_price

                        st.session_state.portfolio['holdings'].append(new_holding)
                        st.success(f"Added ${amount:,.0f} in {name if name else default_name}")
                        st.rerun()
                    else:
                        st.error("Please enter a dollar amount")

    with col2:
        st.subheader("Current Portfolio")
        if st.session_state.portfolio and st.session_state.portfolio.get('holdings'):
            # Display holdings with better formatting
            holdings = st.session_state.portfolio['holdings']
            
            # Normalize holdings for display - add type field if missing
            for h in holdings:
                if 'type' not in h:
                    if 'ticker' in h and h.get('ticker'):
                        h['type'] = 'stock'
                    else:
                        h['type'] = 'other'
            
            # Separate stocks from other investments
            stocks = [h for h in holdings if h.get('type') == 'stock']
            others = [h for h in holdings if h.get('type') != 'stock']
            
            if stocks:
                st.markdown("**📈 Stocks/ETFs:**")
                stock_data = []
                for h in stocks:
                    ticker = h.get('ticker', 'N/A')
                    shares = h.get('shares', 0)
                    price = h.get('purchase_price', '-')
                    stock_data.append({
                        'Ticker': ticker,
                        'Shares': shares,
                        'Purchase Price': f"${price:.2f}" if isinstance(price, (int, float)) and price > 0 else '-'
                    })
                st.dataframe(pd.DataFrame(stock_data), use_container_width=True, hide_index=True)
            
            if others:
                st.markdown("**💵 Other Investments:**")
                other_data = []
                for h in others:
                    inv_type = h.get('type', 'other').upper()
                    name = h.get('name', 'Unknown')
                    amount = h.get('shares', 0)  # For non-stocks, shares = dollar amount
                    rate = h.get('purchase_price', 0)  # For non-stocks, purchase_price = yield/rate
                    other_data.append({
                        'Type': inv_type,
                        'Description': name,
                        'Amount': f"${amount:,.0f}",
                        'Yield/Rate': f"{rate:.2f}%" if rate > 0 else '-'
                    })
                st.dataframe(pd.DataFrame(other_data), use_container_width=True, hide_index=True)

            if st.button("Analyze Current Portfolio"):
                try:
                    with smart_spinner():
                        agent = PortfolioAnalysisAgent()
                        analysis = agent.analyze_portfolio(st.session_state.portfolio)
                        if 'error' in analysis:
                            st.error(f"Analysis error: {analysis['error']}")
                        else:
                            display_portfolio_analysis(analysis)
                except Exception as e:
                    st.error(f"Failed to analyze portfolio: {str(e)}")
                    st.write("Debug - Portfolio data:", st.session_state.portfolio)
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
        rating_abbrev = {
            "Well Diversified": "Well Div.",
            "Moderately Diversified": "Moderate",
            "Somewhat Concentrated": "Concentrated",
            "Highly Concentrated": "Very Conc."
        }
        short_rating = rating_abbrev.get(div_score['rating'], div_score['rating'])
        st.metric(
            "Diversification", 
            short_rating, 
            f"{div_score['score']}/100",
            help=f"Rating: {div_score['rating']} (Score: {div_score['score']}/100). Measures how well your portfolio is spread across sectors."
        )
        st.caption(f"{div_score['rating']}")

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
            # Create stunning 3D-style pie chart with rich colors
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', 
                     '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B739', '#52B788']
            
            fig = go.Figure(data=[go.Pie(
                labels=list(sector_data.keys()),
                values=list(sector_data.values()),
                hole=0.4,  # Donut chart for modern look
                marker=dict(
                    colors=colors[:len(sector_data)],
                    line=dict(color='#FFFFFF', width=3)
                ),
                textposition='outside',
                textinfo='label+percent',
                textfont=dict(size=12, color='#2C3E50', family='Arial Black'),
                hovertemplate='<b>%{label}</b><br>%{value:.1f}%<br>%{percent}<extra></extra>',
                pull=[0.05] * len(sector_data),  # Slight separation for 3D effect
                rotation=45,
                insidetextorientation='radial'
            )])
            
            fig.update_layout(
                title={
                    'text': "Portfolio by Sector",
                    'y':0.95,
                    'x':0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': dict(size=18, color='#2C3E50', family='Arial Black')
                },
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05,
                    font=dict(size=11)
                ),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=450,
                margin=dict(l=20, r=120, t=60, b=20)
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
        
        # Format monetary values with 2 decimals
        display_df['Price'] = display_df['Price'].apply(lambda x: f"${x:,.2f}")
        display_df['Value'] = display_df['Value'].apply(lambda x: f"${x:,.2f}")
        display_df['Gain/Loss'] = display_df['Gain/Loss'].apply(lambda x: f"${x:,.2f}" if x >= 0 else f"-${abs(x):,.2f}")
        display_df['Gain %'] = display_df['Gain %'].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(display_df, use_container_width=True)

        # Add insights about best/worst performers
        best_performer = holdings_df.loc[holdings_df['gain_loss_pct'].idxmax()]
        worst_performer = holdings_df.loc[holdings_df['gain_loss_pct'].idxmin()]

        col1, col2 = st.columns(2)
        with col1:
            st.success(f"🏆 **Best Performer:** {best_performer['ticker']} (+{best_performer['gain_loss_pct']:.1f}%)")
        with col2:
            st.error(f"📉 **Worst Performer:** {worst_performer['ticker']} ({worst_performer['gain_loss_pct']:.1f}%)")

    # Diversification Recommendations with Scores
    st.markdown("---")
    st.markdown("### 💡 Diversification Recommendations")
    st.markdown("""
    Based on your portfolio's current allocation, here are specific investment options to consider for better diversification.
    Each option is scored across multiple factors to help you compare and decide.
    """)
    
    # Generate recommendations
    agent = PortfolioAnalysisAgent()
    recommendations = agent.generate_diversification_recommendations(analysis)
    
    if recommendations:
        for idx, rec in enumerate(recommendations, 1):
            with st.expander(f"**{idx}. {rec['ticker']} - {rec['name']}** (Score: {rec['investment_score']}/100)", expanded=(idx==1)):
                # Header with category and reason
                st.markdown(f"**Category:** {rec['category']}")
                st.markdown(f"**Why Consider:** {rec['reason']}")
                st.markdown(f"**Suggested Allocation:** {rec['allocation_suggestion']}")
                
                # Scores in columns
                st.markdown("#### 📊 Investment Metrics")
                score_col1, score_col2, score_col3 = st.columns(3)
                
                with score_col1:
                    risk = rec['scores']['risk_score']
                    risk_color = "🟢" if risk <= 3 else "🟡" if risk <= 6 else "🔴"
                    st.metric("Risk Level", f"{risk}/10 {risk_color}", help="Lower is safer")
                    
                    st.metric("Return Potential", f"{rec['scores']['return_potential']}/10", help="Higher is better")
                
                with score_col2:
                    st.metric("Diversification Benefit", f"{rec['scores']['diversification_benefit']}/10", help="How much this improves portfolio diversity")
                    
                    st.metric("Liquidity", f"{rec['scores']['liquidity']}/10", help="How easily you can buy/sell")
                
                with score_col3:
                    st.metric("Annual Yield", rec['scores']['annual_yield'], help="Expected annual income/returns")
                    
                    st.metric(
                        "Time Horizon", 
                        rec['scores']['time_horizon'], 
                        help=f"Recommended holding period: {rec['scores']['time_horizon']}"
                    )
                
                # Pros and Cons
                st.markdown("#### ✅ Pros")
                for pro in rec['pros']:
                    st.markdown(f"- {pro}")
                
                st.markdown("#### ⚠️ Cons & Considerations")
                for con in rec['cons']:
                    st.markdown(f"- {con}")
                
                # Overall score visualization
                st.markdown("#### 🎯 Overall Investment Score")
                score = rec['investment_score']
                score_color = "#10b981" if score >= 80 else "#f59e0b" if score >= 70 else "#ef4444"
                st.markdown(f"""
                <div style="background: linear-gradient(to right, {score_color} {score}%, #e5e7eb {score}%);
                            height: 30px; border-radius: 8px; position: relative;">
                    <div style="position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%);
                                color: white; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.5);">
                        {score}/100
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if score >= 80:
                    st.success("⭐ **Highly Recommended** - Strong fit for diversification")
                elif score >= 70:
                    st.info("✔️ **Good Option** - Solid choice for portfolio balance")
                else:
                    st.warning("⚡ **Consider Carefully** - Weigh pros and cons for your situation")
    else:
        st.info("👍 Your portfolio appears well-diversified! Keep monitoring and rebalancing periodically.")
    
    # Educational disclaimer
    st.caption("*These are educational suggestions based on portfolio analysis, not financial advice. Always do your own research and consider consulting a financial advisor before making investment decisions.*")


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

    # Initialize session state for insights loading
    if 'market_insights_loaded' not in st.session_state:
        st.session_state.market_insights_loaded = False
    
    # Show button at top level if data is not loaded
    if not st.session_state.market_insights_loaded:
        st.markdown("---")
        st.info("💡 Click below to load detailed market insights (stocks, indices, sectors, economic indicators & news)")
        st.caption("🔄 Data is cached for 30 minutes for faster subsequent loads")
        if st.button("🚀 Load Market Insights", key="load_insights_btn", type="primary"):
            st.session_state.market_insights_loaded = True
            st.rerun()
    
    # Show expandable section if data is loaded
    if st.session_state.market_insights_loaded:
        # Auto-expand on first load, then user controls it
        initial_expand = st.session_state.get('market_insights_auto_expanded', True)
        
        with st.expander("📊 **Detailed Market Insights** (Top Performers, Trends & News)", expanded=initial_expand):
            # Mark as no longer auto-expanding after first view
            if initial_expand:
                st.session_state.market_insights_auto_expanded = False
            
            # Add a refresh button
            col1, col2 = st.columns([6, 1])
            with col2:
                if st.button("🔄 Refresh", key="refresh_insights_btn", help="Clear cache and reload data"):
                    # Clear all cached data
                    load_top_stocks_performance.clear()
                    load_global_indices_performance.clear()
                    load_sector_performance.clear()
                    load_economic_indicators.clear()
                    load_market_news.clear()
                    st.success("✅ Cache cleared! Reloading...")
                    st.rerun()
            
            st.markdown("### 🏆 Top Stock Performance")
            
            with st.spinner("Loading top performers..."):
                try:
                    # Use cached function
                    df = load_top_stocks_performance()
                    
                    if df is not None:
                        # Display in tabs for different time periods
                        tab1m, tab6m, tabytd, tab5y = st.tabs(["� 1 Month", "📊 6 Months", "📊 YTD", "📊 5 Years"])
                        
                        with tab1m:
                            # Sort by 1 month performance
                            df_sorted = df.copy()
                            df_sorted['1mo_val'] = df_sorted['1 Month'].apply(parse_return)
                            df_sorted = df_sorted.sort_values('1mo_val', ascending=False)
                            
                            # Top 3 and chart
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.markdown("**Top 3 Performers:**")
                                for idx, row in df_sorted.head(3).iterrows():
                                    perf = row['1 Month']
                                    if perf != 'N/A':
                                        val = parse_return(perf)
                                        color = 'green' if val > 0 else 'red'
                                        display_perf = f"{val:.2f}" if val != -999 else perf
                                        st.markdown(f"**{row['Company']}** ({row['Ticker']}): <span style='color:{color}'>{display_perf}%</span>", unsafe_allow_html=True)
                            
                            with col2:
                                # Bar chart
                                chart_df = df_sorted[df_sorted['1mo_val'] != -999].copy()
                                fig = px.bar(
                                    chart_df,
                                    x='Ticker',
                                    y='1mo_val',
                                    title='1 Month Performance (%)',
                                    color='1mo_val',
                                    color_continuous_scale='RdYlGn',
                                    labels={'1mo_val': 'Return (%)'}
                                )
                                fig.update_layout(showlegend=False, height=300)
                                st.plotly_chart(fig, use_container_width=True)
                        
                        with tab6m:
                            df_sorted = df.copy()
                            df_sorted['6mo_val'] = df_sorted['6 Months'].apply(parse_return)
                            df_sorted = df_sorted.sort_values('6mo_val', ascending=False)
                            
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.markdown("**Top 3 Performers:**")
                                for idx, row in df_sorted.head(3).iterrows():
                                    perf = row['6 Months']
                                    if perf != 'N/A':
                                        val = parse_return(perf)
                                        color = 'green' if val > 0 else 'red'
                                        display_perf = f"{val:.2f}" if val != -999 else perf
                                        st.markdown(f"**{row['Company']}** ({row['Ticker']}): <span style='color:{color}'>{display_perf}%</span>", unsafe_allow_html=True)
                            
                            with col2:
                                chart_df = df_sorted[df_sorted['6mo_val'] != -999].copy()
                                fig = px.bar(
                                    chart_df,
                                    x='Ticker',
                                    y='6mo_val',
                                    title='6 Month Performance (%)',
                                    color='6mo_val',
                                    color_continuous_scale='RdYlGn',
                                    labels={'6mo_val': 'Return (%)'}
                                )
                                fig.update_layout(showlegend=False, height=300)
                                st.plotly_chart(fig, use_container_width=True)
                        
                        with tabytd:
                            df_sorted = df.copy()
                            df_sorted['ytd_val'] = df_sorted['YTD'].apply(parse_return)
                            df_sorted = df_sorted.sort_values('ytd_val', ascending=False)
                            
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.markdown("**Top 3 Performers:**")
                                for idx, row in df_sorted.head(3).iterrows():
                                    perf = row['YTD']
                                    if perf != 'N/A':
                                        val = parse_return(perf)
                                        color = 'green' if val > 0 else 'red'
                                        display_perf = f"{val:.2f}" if val != -999 else perf
                                        st.markdown(f"**{row['Company']}** ({row['Ticker']}): <span style='color:{color}'>{display_perf}%</span>", unsafe_allow_html=True)
                            
                            with col2:
                                chart_df = df_sorted[df_sorted['ytd_val'] != -999].copy()
                                fig = px.bar(
                                    chart_df,
                                    x='Ticker',
                                    y='ytd_val',
                                    title='YTD Performance (%)',
                                    color='ytd_val',
                                    color_continuous_scale='RdYlGn',
                                    labels={'ytd_val': 'Return (%)'}
                                )
                                fig.update_layout(showlegend=False, height=300)
                                st.plotly_chart(fig, use_container_width=True)
                        
                        with tab5y:
                            df_sorted = df.copy()
                            df_sorted['5y_val'] = df_sorted['5 Years'].apply(parse_return)
                            df_sorted = df_sorted.sort_values('5y_val', ascending=False)
                            
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.markdown("**Top 3 Performers:**")
                                for idx, row in df_sorted.head(3).iterrows():
                                    perf = row['5 Years']
                                    if perf != 'N/A':
                                        val = parse_return(perf)
                                        color = 'green' if val > 0 else 'red'
                                        display_perf = f"{val:.2f}" if val != -999 else perf
                                        st.markdown(f"**{row['Company']}** ({row['Ticker']}): <span style='color:{color}'>{display_perf}%</span>", unsafe_allow_html=True)
                            
                            with col2:
                                chart_df = df_sorted[df_sorted['5y_val'] != -999].copy()
                                fig = px.bar(
                                    chart_df,
                                    x='Ticker',
                                    y='5y_val',
                                    title='5 Year Performance (%)',
                                    color='5y_val',
                                    color_continuous_scale='RdYlGn',
                                    labels={'5y_val': 'Return (%)'}
                                )
                                fig.update_layout(showlegend=False, height=300)
                                st.plotly_chart(fig, use_container_width=True)
                        
                        # Full comparison table
                        st.markdown("---")
                        st.markdown("**📋 Complete Performance Table:**")
                        st.dataframe(df[['Ticker', 'Company', 'Price', '1 Month', '6 Months', 'YTD', '5 Years']], use_container_width=True, hide_index=True)
                
                except Exception as e:
                    st.error(f"Error loading performance data: {str(e)}")
            
            st.markdown("---")
            st.markdown("### 🌍 Global Market Indices")
            
            with st.spinner("Loading global indices..."):
                try:
                    # Use cached function
                    df_indices = load_global_indices_performance()
                    
                    if df_indices is not None:
                        # Display in tabs for different time periods
                        idx_tab1m, idx_tab6m, idx_tabytd, idx_tab5y = st.tabs(["� 1 Month", "📊 6 Months", "📊 YTD", "📊 5 Years"])
                    
                    with idx_tab1m:
                        df_sorted = df_indices.copy()
                        df_sorted['1mo_val'] = df_sorted['1 Month'].apply(parse_return)
                        df_sorted = df_sorted.sort_values('1mo_val', ascending=False)
                        
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.markdown("**Top 3 Indices:**")
                            for idx, row in df_sorted.head(3).iterrows():
                                perf = row['1 Month']
                                if perf != 'N/A':
                                    val = parse_return(perf)
                                    color = 'green' if val > 0 else 'red'
                                    display_perf = f"{val:.2f}" if val != -999 else perf
                                    st.markdown(f"**{row['Index']}**: <span style='color:{color}'>{display_perf}%</span>", unsafe_allow_html=True)
                        
                        with col2:
                            chart_df = df_sorted[df_sorted['1mo_val'] != -999].copy()
                            fig = go.Figure(data=[
                                go.Bar(
                                    x=chart_df['Index'],
                                    y=chart_df['1mo_val'],
                                    marker=dict(
                                        color=chart_df['1mo_val'],
                                        colorscale='RdYlGn',
                                        line=dict(color='#333', width=1)
                                    ),
                                    text=chart_df['1mo_val'].apply(lambda x: f"{x:.1f}%"),
                                    textposition='outside'
                                )
                            ])
                            fig.update_layout(
                                title='1 Month Performance (%)',
                                showlegend=False,
                                height=350,
                                xaxis_tickangle=-45,
                                yaxis_title='Return (%)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)'
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with idx_tab6m:
                        df_sorted = df_indices.copy()
                        df_sorted['6mo_val'] = df_sorted['6 Months'].apply(parse_return)
                        df_sorted = df_sorted.sort_values('6mo_val', ascending=False)
                        
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.markdown("**Top 3 Indices:**")
                            for idx, row in df_sorted.head(3).iterrows():
                                perf = row['6 Months']
                                if perf != 'N/A':
                                    val = parse_return(perf)
                                    color = 'green' if val > 0 else 'red'
                                    display_perf = f"{val:.2f}" if val != -999 else perf
                                    st.markdown(f"**{row['Index']}**: <span style='color:{color}'>{display_perf}%</span>", unsafe_allow_html=True)
                        
                        with col2:
                            chart_df = df_sorted[df_sorted['6mo_val'] != -999].copy()
                            fig = go.Figure(data=[
                                go.Bar(
                                    x=chart_df['Index'],
                                    y=chart_df['6mo_val'],
                                    marker=dict(
                                        color=chart_df['6mo_val'],
                                        colorscale='RdYlGn',
                                        line=dict(color='#333', width=1)
                                    ),
                                    text=chart_df['6mo_val'].apply(lambda x: f"{x:.1f}%"),
                                    textposition='outside'
                                )
                            ])
                            fig.update_layout(
                                title='6 Month Performance (%)',
                                showlegend=False,
                                height=350,
                                xaxis_tickangle=-45,
                                yaxis_title='Return (%)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)'
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with idx_tabytd:
                        df_sorted = df_indices.copy()
                        df_sorted['ytd_val'] = df_sorted['YTD'].apply(parse_return)
                        df_sorted = df_sorted.sort_values('ytd_val', ascending=False)
                        
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.markdown("**Top 3 Indices:**")
                            for idx, row in df_sorted.head(3).iterrows():
                                perf = row['YTD']
                                if perf != 'N/A':
                                    val = parse_return(perf)
                                    color = 'green' if val > 0 else 'red'
                                    display_perf = f"{val:.2f}" if val != -999 else perf
                                    st.markdown(f"**{row['Index']}**: <span style='color:{color}'>{display_perf}%</span>", unsafe_allow_html=True)
                        
                        with col2:
                            chart_df = df_sorted[df_sorted['ytd_val'] != -999].copy()
                            fig = go.Figure(data=[
                                go.Bar(
                                    x=chart_df['Index'],
                                    y=chart_df['ytd_val'],
                                    marker=dict(
                                        color=chart_df['ytd_val'],
                                        colorscale='RdYlGn',
                                        line=dict(color='#333', width=1)
                                    ),
                                    text=chart_df['ytd_val'].apply(lambda x: f"{x:.1f}%"),
                                    textposition='outside'
                                )
                            ])
                            fig.update_layout(
                                title='YTD Performance (%)',
                                showlegend=False,
                                height=350,
                                xaxis_tickangle=-45,
                                yaxis_title='Return (%)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)'
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with idx_tab5y:
                        df_sorted = df_indices.copy()
                        df_sorted['5y_val'] = df_sorted['5 Years'].apply(parse_return)
                        df_sorted = df_sorted.sort_values('5y_val', ascending=False)
                        
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.markdown("**Top 3 Indices:**")
                            for idx, row in df_sorted.head(3).iterrows():
                                perf = row['5 Years']
                                if perf != 'N/A':
                                    val = parse_return(perf)
                                    color = 'green' if val > 0 else 'red'
                                    display_perf = f"{val:.2f}" if val != -999 else perf
                                    st.markdown(f"**{row['Index']}**: <span style='color:{color}'>{display_perf}%</span>", unsafe_allow_html=True)
                        
                        with col2:
                            chart_df = df_sorted[df_sorted['5y_val'] != -999].copy()
                            fig = go.Figure(data=[
                                go.Bar(
                                    x=chart_df['Index'],
                                    y=chart_df['5y_val'],
                                    marker=dict(
                                        color=chart_df['5y_val'],
                                        colorscale='RdYlGn',
                                        line=dict(color='#333', width=1)
                                    ),
                                    text=chart_df['5y_val'].apply(lambda x: f"{x:.1f}%"),
                                    textposition='outside'
                                )
                            ])
                            fig.update_layout(
                                title='5 Year Performance (%)',
                                showlegend=False,
                                height=350,
                                xaxis_tickangle=-45,
                                yaxis_title='Return (%)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)'
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    
                    # Full comparison table
                    st.markdown("---")
                    st.markdown("**📋 Complete Indices Table:**")
                    st.dataframe(df_indices[['Index', 'Level', '1 Month', '6 Months', 'YTD', '5 Years']], use_container_width=True, hide_index=True)
                
                except Exception as e:
                    st.error(f"Error loading indices data: {str(e)}")
            
            st.markdown("---")
            st.markdown("### 🏭 US Sector & Industry Performance")
            st.caption("Track major sectors and industries to get a pulse on the economy")
            
            with st.spinner("Loading sector performance..."):
                try:
                    # Use cached function
                    df_sectors, sectors_industries = load_sector_performance()
                    
                    if df_sectors is not None:
                        # Create tabbed visualization for different time periods
                        st.markdown("**📊 Sector Performance Across Time Periods:**")
                        
                        sector_tabs = st.tabs(["� 1 Month", "📈 6 Months", "📈 YTD", "📈 5 Years"])
                        
                        time_periods = [
                            ('1mo', '1 Month', sector_tabs[0]),
                            ('6mo', '6 Months', sector_tabs[1]),
                            ('ytd', 'YTD', sector_tabs[2]),
                            ('5y', '5 Year', sector_tabs[3])
                        ]
                        
                        for period_key, period_name, tab in time_periods:
                            with tab:
                                # Prepare data for this period
                                period_data = []
                                for sector_name in sectors_industries.keys():
                                    sector_df = df_sectors[df_sectors['Sector'] == sector_name].copy()
                                    if not sector_df.empty:
                                        sector_df[f'{period_key}_val'] = sector_df[period_key].apply(parse_return)
                                        avg_return = sector_df[f'{period_key}_val'][sector_df[f'{period_key}_val'] != -999].mean()
                                        if not pd.isna(avg_return):
                                            period_data.append({
                                                'Sector': sector_name,
                                                'Return (%)': avg_return
                                            })
                                
                                if period_data:
                                    period_df = pd.DataFrame(period_data).sort_values('Return (%)', ascending=False)
                                    
                                    # Create horizontal bar chart
                                    fig = go.Figure(data=[
                                        go.Bar(
                                            y=period_df['Sector'],
                                            x=period_df['Return (%)'],
                                            orientation='h',
                                            marker=dict(
                                                color=period_df['Return (%)'],
                                                colorscale='RdYlGn',
                                                line=dict(color='#333', width=1),
                                                colorbar=dict(title="Return %")
                                            ),
                                            text=period_df['Return (%)'].apply(lambda x: f"{x:.1f}%"),
                                            textposition='outside'
                                        )
                                    ])
                                    fig.update_layout(
                                        title=f'Average {period_name} Performance by Sector/Industry',
                                        showlegend=False,
                                        height=400,
                                        xaxis_title='Return (%)',
                                        plot_bgcolor='rgba(0,0,0,0)',
                                        paper_bgcolor='rgba(0,0,0,0)',
                                        margin=dict(l=200)
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.warning(f"No data available for {period_name}")
                        
                        # Detailed table
                        st.markdown("**📋 Detailed Sector Breakdown:**")
                        st.dataframe(
                            df_sectors[['Sector', 'Asset', 'Price', '1mo', '6mo', 'ytd', '5y']], 
                        use_container_width=True, 
                        hide_index=True
                    )
                    
                except Exception as e:
                    st.error(f"Error loading sector data: {str(e)}")
            
            st.markdown("---")
            st.markdown("### 📊 Key Economic Indicators")
            st.caption("What economists watch to gauge economic health")
            
            with st.spinner("Loading economic indicators..."):
                try:
                    # Use cached function
                    economic_data = load_economic_indicators()
                    
                    if economic_data:
                        # Display in cards
                        for indicator in economic_data:
                            with st.container():
                                col1, col2, col3 = st.columns([2, 3, 1])
                                with col1:
                                    st.markdown(f"**{indicator['Indicator']}**")
                                with col2:
                                    st.markdown(f"{indicator['Value']}")
                                    st.caption(indicator['Significance'])
                                with col3:
                                    st.markdown(indicator['Status'])
                                    st.markdown("")
                        
                        # Add note about inflation
                        st.info("**💡 Note on Inflation:** CPI (Consumer Price Index) data is released monthly by the Bureau of Labor Statistics. Current inflation trends can be tracked through commodity prices, Treasury yields, and the Fed's statements. Target rate: ~2%")
                    else:
                        st.warning("Unable to load economic indicators at this time")
                except Exception as e:
                    st.error(f"Error loading economic indicators: {str(e)}")
            
            st.markdown("---")
            st.markdown("### 📰 Latest Market News")
            
            # Get news from a major index or general market
            with st.spinner("Loading latest news..."):
                try:
                    # Use cached function
                    news_items = load_market_news()
                    
                    if news_items:
                        # Display top 5 news items in a clean format
                        for idx, item in enumerate(news_items[:5], 1):
                            with st.container():
                                col1, col2 = st.columns([4, 1])
                                with col1:
                                    st.markdown(f"**{idx}. {item['title']}**")
                                    st.caption(f"🏢 {item['publisher']} • 🕒 {item.get('published', 'Recently')}")
                                with col2:
                                    st.markdown(f"[Read →]({item['link']})")
                                st.markdown("")
                    else:
                        st.info("No market news available at the moment")
                except Exception as e:
                    st.warning(f"Unable to load news: {str(e)}")

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
                        "� 1 Month", "📈 6 Months", "📈 YTD", "📈 1 Year", "📈 5 Years"
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
    
    # Check if we have pre-loaded data from chat and haven't used it yet
    preload_data = st.session_state.preload_data
    has_preload = bool(preload_data)
    
    # Initialize form values in session state if not present or if we have new preload data
    if 'goal_form_initialized' not in st.session_state or has_preload:
        # Set defaults from preload data if available, otherwise use standard defaults
        st.session_state.goal_target = int(preload_data.get('target_amount', 100000))
        st.session_state.goal_current = int(preload_data.get('current_savings', 10000))
        st.session_state.goal_monthly = int(preload_data.get('monthly_contribution', 500))
        st.session_state.goal_years = int(preload_data.get('years_to_goal', 10))
        st.session_state.goal_risk = preload_data.get('risk_tolerance', 'moderate')
        st.session_state.goal_type = preload_data.get('goal_type', 'retirement')
        st.session_state.goal_form_initialized = True
        
        # Show success message if values were pre-filled from chat
        if has_preload:
            preload_msgs = []
            if 'target_amount' in preload_data:
                preload_msgs.append(f"Target: ${st.session_state.goal_target:,}")
            if 'current_savings' in preload_data:
                preload_msgs.append(f"Current Savings: ${st.session_state.goal_current:,}")
            if 'monthly_contribution' in preload_data:
                preload_msgs.append(f"Monthly: ${st.session_state.goal_monthly:,}")
            if 'years_to_goal' in preload_data:
                preload_msgs.append(f"Years: {st.session_state.goal_years}")
            
            if preload_msgs:
                st.success(f"✨ Pre-filled from your question: {' | '.join(preload_msgs)}")
            
            # Clear preload data after using it
            st.session_state.preload_data = {}

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Goal Parameters")

        # Map goal_type to display name
        goal_type_options = ["Retirement", "House Down Payment", "Education", "Emergency Fund", "Other"]
        goal_type_map = {
            'retirement': 'Retirement',
            'house': 'House Down Payment',
            'education': 'Education',
            'emergency': 'Emergency Fund',
            'general': 'Other'
        }
        default_goal_display = goal_type_map.get(st.session_state.goal_type, 'Retirement')
        default_goal_index = goal_type_options.index(default_goal_display) if default_goal_display in goal_type_options else 0

        goal_type = st.selectbox(
            "Goal Type",
            goal_type_options,
            index=default_goal_index,
            key="goal_type_select"
        )

        target_amount = st.number_input(
            "Target Amount ($)",
            min_value=0,
            value=st.session_state.goal_target,
            step=10000,
            key="goal_target_amount"
        )

        current_savings = st.number_input(
            "Current Savings ($)",
            min_value=0,
            value=st.session_state.goal_current,
            step=1000,
            key="goal_current_savings"
        )

        monthly_contribution = st.number_input(
            "Monthly Contribution ($)",
            min_value=0,
            value=st.session_state.goal_monthly,
            step=100,
            key="goal_monthly_contribution"
        )

        years = st.slider(
            "Years Until Goal",
            min_value=1,
            max_value=40,
            value=st.session_state.goal_years,
            key="goal_years_slider"
        )

        # Map risk_tolerance to display value
        risk_options = ["Conservative (4%)", "Moderate (6%)", "Aggressive (8%)"]
        risk_map = {
            'conservative': 0,
            'moderate': 1,
            'aggressive': 2
        }
        default_risk_index = risk_map.get(st.session_state.goal_risk, 1)

        risk_level = st.select_slider(
            "Risk Tolerance",
            options=risk_options,
            value=risk_options[default_risk_index],
            key="goal_risk_slider"
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
        # Try to extract portfolio holdings from the query
        parsed_holdings = extract_portfolio_from_query(query)
        if parsed_holdings:
            # Store the parsed portfolio in session state
            st.session_state.portfolio = {'holdings': parsed_holdings}
            link_text = "View portfolio breakdown"
            message_text = "Want to see detailed portfolio analysis with charts?"
        elif st.session_state.portfolio:
            link_text = "View portfolio breakdown"
            message_text = "Want to see detailed portfolio analysis with charts?"
        else:
            link_text = "Go to Portfolio tab"
            message_text = "Upload your portfolio to see detailed analysis"

    elif primary_agent == 'goal_planning':
        # Try to extract goal parameters from the agent's output
        goal_params = None
        agent_outputs = result.get("agent_outputs", {})
        if "goal_planning" in agent_outputs:
            goal_params = agent_outputs["goal_planning"].get("goal_params")
        
        if goal_params:
            # Store all extracted parameters
            if goal_params.get('target_amount'):
                preload_data['target_amount'] = goal_params['target_amount']
            if goal_params.get('current_savings'):
                preload_data['current_savings'] = goal_params['current_savings']
            if goal_params.get('monthly_contribution'):
                preload_data['monthly_contribution'] = goal_params['monthly_contribution']
            if goal_params.get('years_to_goal'):
                preload_data['years_to_goal'] = goal_params['years_to_goal']
            if goal_params.get('risk_tolerance'):
                preload_data['risk_tolerance'] = goal_params['risk_tolerance']
            if goal_params.get('goal_type'):
                preload_data['goal_type'] = goal_params['goal_type']
            
            target_amount = goal_params.get('target_amount', 0)
            link_text = f"Visualize ${target_amount:,.0f} goal" if target_amount else "Visualize your goal"
            message_text = f"Want to see growth projections for your ${target_amount:,.0f} goal?" if target_amount else "Want to visualize your financial goal with detailed projections?"
        else:
            # Fallback to extracting just dollar amount from query
            goal_amount = extract_dollar_amount(query)
            if goal_amount:
                preload_data['target_amount'] = goal_amount
                link_text = f"Visualize ${goal_amount:,.0f} goal"
                message_text = f"Want to see growth projections for your ${goal_amount:,.0f} goal?"
            else:
                link_text = "Plan your goal"
                message_text = "Want to visualize your financial goal with detailed projections?"

    elif primary_agent == 'news_synthesizer':
        link_text = "View latest market news"
        message_text = "Want to see market insights, trends, and recent news?"

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
    Extract ticker symbol from user query using LLM semantic understanding.

    Args:
        query: User's question

    Returns:
        Ticker symbol if found, None otherwise
    """
    import re
    import json
    from src.core.llm import LLMManager

    # Quick check for explicit $ ticker mentions (e.g., $AAPL)
    dollar_match = re.search(r'\$([A-Z]{1,5})\b', query.upper())
    if dollar_match:
        return dollar_match.group(1)

    # Use LLM for semantic extraction
    llm = LLMManager(temperature=0)
    
    extraction_prompt = f"""Extract the stock ticker symbol mentioned in this question.
Only return a ticker if the user is specifically asking about a particular company or stock.
Do NOT extract tickers from general market questions.

Question: "{query}"

Rules:
1. Return ONLY the ticker symbol (e.g., "AAPL", "MSFT", "TSLA") if a specific company/stock is mentioned
2. Return "NONE" if this is a general market question (e.g., "how are markets doing", "world markets")
3. Return "NONE" if no specific company or ticker is mentioned
4. Common companies: Apple=AAPL, Microsoft=MSFT, Google=GOOGL, Tesla=TSLA, Amazon=AMZN, Meta=META, Nvidia=NVDA

Return only the ticker symbol or "NONE", nothing else."""

    try:
        response = llm.generate(extraction_prompt).strip().upper()
        
        # Clean response
        if response.startswith('```'):
            response = response.split('```')[1] if '```' in response[3:] else response[3:]
        response = response.strip()
        
        # Validate response
        if response == "NONE" or not response:
            return None
        
        # Check if it looks like a valid ticker (1-5 uppercase letters)
        if re.match(r'^[A-Z]{1,5}$', response):
            return response
        
        return None
        
    except Exception as e:
        print(f"Ticker extraction error: {e}")
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

    # Exclude retirement account names that contain numbers + k (like 401k, 403b, 457, etc.)
    retirement_accounts = [
        r'\b401[k(]',  # 401k or 401(k)
        r'\b403[b(]',  # 403b or 403(b)
        r'\b457\b',    # 457 plan
        r'\bIRA\b',    # IRA
        r'\bRoth\b',   # Roth
    ]

    # Check if query contains retirement account references
    for account_pattern in retirement_accounts:
        if re.search(account_pattern, query, re.IGNORECASE):
            # If we find retirement account terms, be more strict about what we extract
            # Only match explicit dollar signs to avoid confusion
            strict_patterns = [
                r'\$([0-9,]+\.?[0-9]*)\s*(?:million|M)',  # $1.5M, $1 million
                r'\$([0-9,]+\.?[0-9]*)\s*(?:thousand|K)',  # $100K, $100 thousand
                r'\$([0-9,]+\.?[0-9]*)',  # $100,000
            ]

            for pattern in strict_patterns:
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
            return None  # Don't try looser patterns if retirement accounts mentioned

    # Look for patterns like $100,000 or $1M or 100k (if no retirement accounts mentioned)
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


def extract_portfolio_from_query(query: str) -> Optional[List[Dict[str, Any]]]:
    """
    Extract portfolio holdings from a natural language query using LLM semantic understanding.
    
    Uses the LLM to parse natural language and identify:
    - Stock/ETF tickers with share counts
    - Bonds, CDs, and other fixed-income investments (dollar amounts)
    - Cash holdings (HYSA, savings accounts, etc.)
    - Other investments without tickers (real estate, crypto, etc.)
    
    Args:
        query: User's question containing portfolio details
    
    Returns:
        List of holdings dicts with type, ticker/name, amount, and optional purchase_price
    """
    import json
    from src.core.llm import LLMManager
    
    # Create LLM instance with low temperature for consistent extraction
    llm = LLMManager(temperature=0)
    
    extraction_prompt = f"""Extract portfolio holdings from the following text. 
Identify ALL types of investments including stocks, bonds, cash, CDs, and other assets.

Text: "{query}"

Return a JSON array of holdings. Each holding should have:
- type: Investment type - one of: "stock", "bond", "cash", "cd", "other"
- ticker: Stock ticker (e.g., "VOO") for stocks, or null for bonds/cash/other
- name: Descriptive name for non-stock investments (e.g., "Treasury Bonds", "High Yield Savings", "CD 5-year")
- shares: Number of shares for stocks, or dollar amount for bonds/cash/other
- purchase_price: (optional) Purchase price per share for stocks, OR interest rate/yield percentage for bonds/CDs/cash
- purchase_date: (optional) Purchase date or year as string (e.g., "2015", "2019", "Jan 2020")

Rules:
1. For STOCKS/ETFs: type="stock", ticker="AAPL", shares=number of shares, purchase_price=price per share
2. For BONDS: type="bond", ticker=null, name="Treasury Bonds" or "Corporate Bonds", shares=dollar amount, purchase_price=yield % if mentioned
3. For CASH/HYSA: type="cash", ticker=null, name="HYSA" or "Savings Account", shares=dollar amount, purchase_price=interest rate % if mentioned (e.g., "4.5%" → 4.5), purchase_date=year/date if mentioned
4. For CDs: type="cd", ticker=null, name="CD 1-year" or "Certificate of Deposit", shares=dollar amount, purchase_price=rate % if mentioned, purchase_date=year/date if mentioned
5. For OTHER: type="other", ticker=null, name=description, shares=dollar amount
6. DO NOT extract common words like "OF", "AT", "IN" as tickers
7. Convert amounts: "50k"→50000, "1M"→1000000
8. Extract percentage rates: "4.5%" → 4.5, "at 3.2%" → 3.2
9. Extract purchase dates/years: "since 2015" → "2015", "from 2019" → "2019", "in Jan 2020" → "2020"
10. If no portfolio mentioned, return empty array []

Return ONLY the JSON array, no other text.

Example outputs:
[{{"type": "stock", "ticker": "VOO", "shares": 300, "purchase_price": 98, "purchase_date": "2019"}}, {{"type": "bond", "ticker": null, "name": "Treasury Bonds", "shares": 25000, "purchase_price": 3.8}}, {{"type": "cash", "ticker": null, "name": "HYSA", "shares": 50000, "purchase_price": 4.5, "purchase_date": "2015"}}]
[]"""
    
    try:
        response = llm.generate(extraction_prompt)
        
        # Extract JSON from response (LLM might add markdown formatting)
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        if response.startswith('```'):
            response = response[3:]
        if response.endswith('```'):
            response = response[:-3]
        response = response.strip()
        
        # Parse JSON
        holdings = json.loads(response)
        
        # Validate and clean the results
        validated_holdings = []
        for holding in holdings:
            if not isinstance(holding, dict):
                continue
            if 'type' not in holding or 'shares' not in holding:
                continue
            
            inv_type = str(holding['type']).lower()
            if inv_type not in ['stock', 'bond', 'cash', 'cd', 'other']:
                continue
            
            try:
                shares = float(holding['shares'])
                validated_holding = {
                    'type': inv_type,
                    'shares': shares
                }
                
                # For stocks, ticker is required
                if inv_type == 'stock':
                    if 'ticker' not in holding or not holding['ticker']:
                        continue
                    ticker = str(holding['ticker']).upper()
                    if not ticker or len(ticker) > 5:
                        continue
                    validated_holding['ticker'] = ticker
                else:
                    # For non-stocks, name is required
                    if 'name' not in holding or not holding['name']:
                        # Generate default name
                        name_map = {'bond': 'Bonds', 'cash': 'Cash', 'cd': 'CD', 'other': 'Other Investment'}
                        validated_holding['name'] = name_map.get(inv_type, 'Investment')
                    else:
                        validated_holding['name'] = str(holding['name'])
                
                # Add purchase price if present
                if 'purchase_price' in holding and holding['purchase_price']:
                    validated_holding['purchase_price'] = float(holding['purchase_price'])
                
                # Add purchase date if present
                if 'purchase_date' in holding and holding['purchase_date']:
                    validated_holding['purchase_date'] = str(holding['purchase_date'])
                
                validated_holdings.append(validated_holding)
            except (ValueError, TypeError):
                continue
        
        return validated_holdings if validated_holdings else None
        
    except Exception as e:
        # Fallback to None if LLM extraction fails
        print(f"Portfolio extraction error: {e}")
        return None



def load_sample_portfolio():
    """Load a sample portfolio for demonstration."""
    st.session_state.portfolio = {
        'holdings': [
            {'type': 'stock', 'ticker': 'VTI', 'shares': 50, 'purchase_price': 200},
            {'type': 'stock', 'ticker': 'VXUS', 'shares': 30, 'purchase_price': 55},
            {'type': 'stock', 'ticker': 'BND', 'shares': 40, 'purchase_price': 75},
            {'type': 'stock', 'ticker': 'AAPL', 'shares': 10, 'purchase_price': 150},
            {'type': 'stock', 'ticker': 'MSFT', 'shares': 8, 'purchase_price': 280},
            {'type': 'cash', 'name': 'High Yield Savings', 'shares': 50000, 'purchase_price': 4.5},
            {'type': 'bond', 'name': 'Treasury Bonds', 'shares': 25000, 'purchase_price': 3.8},
        ]
    }


if __name__ == "__main__":
    # Lazy load imports on first actual use
    lazy_import()
    main()
