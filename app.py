import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from data_collector import StockDataCollector
from database import DatabaseManager
from analysis import PortfolioAnalyzer
import yfinance as yf
from yaml_exporter import StockDataYAMLExporter
import yaml
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="Portfolio Manager",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database if empty
def ensure_database_initialized():
    try:
        db = DatabaseManager()
        positions = db.get_all_positions()
        if not positions:
            logger.info("Database is empty, initializing with test data...")
            from debug.init_test_data import init_test_portfolio
            init_test_portfolio()
            logger.info("Database initialized successfully")
        else:
            logger.info(f"Database already contains {len(positions)} positions")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")

# Initialize database
ensure_database_initialized()

# Custom CSS for styling
st.markdown("""
<style>
    /* Navigation styling */
    div.stRadio > div[role="radiogroup"] {
        padding: 0;
        margin: 0;
        border: none;
    }
    
    div.stRadio > div[role="radiogroup"] > label {
        padding: 10px 15px;
        margin: 0;
        font-size: 18px !important;
        font-weight: 500;
        background: transparent;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    div.stRadio > div[role="radiogroup"] > label:hover {
        background: rgba(151, 166, 195, 0.15);
    }
    
    /* Hide radio button circles */
    div.stRadio > div[role="radiogroup"] > label > div:first-child {
        display: none;
    }
    
    /* Headers */
    h1 {
        font-size: 32px !important;
        padding-bottom: 20px !important;
    }
    
    h2 {
        font-size: 24px !important;
        padding-bottom: 15px !important;
    }
    
    h3 {
        font-size: 20px !important;
        padding-bottom: 10px !important;
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] > div {
        font-size: 24px !important;
    }
</style>
""", unsafe_allow_html=True)

# Load custom CSS
def load_css():
    with open(os.path.join(os.path.dirname(__file__), "style.css")) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Initialize services - remove caching for database operations
collector = StockDataCollector()
db = DatabaseManager()
analyzer = PortfolioAnalyzer()
yaml_exporter = StockDataYAMLExporter()

def refresh_portfolio_data(portfolio_id):
    """Refresh portfolio data from the database"""
    portfolio_data = []
    if portfolio_id:
        positions = db.get_portfolio_positions(portfolio_id)
        for position in positions:
            market_data = db.get_market_data(position.id)
            if market_data and market_data.current_price:
                current_value = position.quantity * market_data.current_price
                cost_basis = position.quantity * position.entry_price
                pnl = current_value - cost_basis
                pnl_pct = (pnl / cost_basis * 100) if cost_basis != 0 else 0
                
                portfolio_data.append({
                    'id': position.id,
                    'ticker': position.ticker,
                    'quantity': position.quantity,
                    'entry_price': position.entry_price,
                    'current_price': market_data.current_price,
                    'current_value': current_value,
                    'cost_basis': cost_basis,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'day_change': (market_data.current_price - market_data.day_low) / market_data.day_low * 100 if market_data.day_low else 0,
                    'sector': getattr(market_data, 'sector', 'N/A'),
                    'pe_ratio': getattr(market_data, 'pe_ratio', None),
                    'dividend_yield': getattr(market_data, 'dividend_yield', None),
                    'rsi': getattr(market_data, 'rsi', None),
                    'notes': position.notes
                })
    return portfolio_data

def format_large_number(num):
    if num is None:
        return "N/A"
    if num >= 1_000_000_000:
        return f"${num/1_000_000_000:.2f}B"
    if num >= 1_000_000:
        return f"${num/1_000_000:.2f}M"
    return f"${num:,.2f}"

# Add error handling for data fetching
def fetch_stock_data_with_feedback(collector, ticker, position_id, force_refresh=False):
    with st.spinner(f'Fetching data for {ticker}...'):
        data = collector.get_stock_data(ticker, position_id, force_refresh=force_refresh)
        if data is None:
            st.warning(f"⚠️ Temporarily unable to fetch data for {ticker}. Using cached data if available.")
        return data

def fetch_historical_data_with_feedback(collector, ticker, period="1y"):
    """Fetch historical data in chunks to avoid rate limiting"""
    with st.spinner(f'Fetching historical data for {ticker}...'):
        # Split the period into smaller chunks
        if period == "5y":
            chunks = ["1y", "2y", "3y", "4y", "5y"]
        elif period == "1y":
            chunks = ["3mo", "6mo", "9mo", "1y"]
        else:
            chunks = [period]
        
        all_data = pd.DataFrame()
        progress_bar = st.progress(0)
        
        for i, chunk in enumerate(chunks):
            data = collector.get_historical_prices(ticker, chunk)
            if data is not None:
                chunk_df = pd.DataFrame(data).sort_index()
                all_data = pd.concat([all_data, chunk_df[~chunk_df.index.isin(all_data.index)]])
            progress_bar.progress((i + 1) / len(chunks))
            time.sleep(2)  # Add delay between chunks
        
        progress_bar.empty()
        
        if all_data.empty:
            st.warning(f"⚠️ Temporarily unable to fetch historical data for {ticker}. Please try again later.")
            return None
        return all_data

def fetch_technical_data_with_feedback(collector, ticker, position_id):
    """Fetch technical indicators with progress feedback"""
    with st.spinner(f'Calculating technical indicators for {ticker}...'):
        data = collector.get_technical_indicators(ticker, position_id)
        if data is None:
            st.warning(f"⚠️ Unable to calculate technical indicators for {ticker}.")
        return data

# Create sidebar for navigation and filters
st.sidebar.title("📊 Portfolio Manager")

# Initialize session state for portfolio management
if 'current_portfolio_id' not in st.session_state:
    db = DatabaseManager()
    default_portfolio = db.get_default_portfolio()
    st.session_state.current_portfolio_id = default_portfolio.id if default_portfolio else None
    db.close()

# Navigation
page = st.sidebar.radio(
    "Navigation",
    ["Portfolios", "Portfolio Overview", "Individual Stock View", "Technical Alerts", "Position Management", "AI Export"],
    index=1  # Default to Portfolio Overview
)

# CSV upload/edit support
st.sidebar.header("Upload Portfolio CSV")
uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type=["csv"], key="portfolio_csv_upload")
if uploaded_file is not None:
    df_csv = pd.read_csv(uploaded_file)
    st.session_state['portfolio_csv'] = df_csv
    st.success("Portfolio CSV uploaded! Reload the page to use this data.")
    # Optionally, update the database with new positions here
elif 'portfolio_csv' not in st.session_state:
    # If no upload and not already in session state, try to load from disk
    csv_path = os.path.join(os.path.dirname(__file__), "portfolio.csv")
    if os.path.exists(csv_path):
        df_csv = pd.read_csv(csv_path)
        st.session_state['portfolio_csv'] = df_csv
    else:
        st.session_state['portfolio_csv'] = pd.DataFrame()

# Add a button to export current portfolio to CSV
if st.sidebar.button("Export Portfolio to CSV"):
    positions = db.get_all_positions()
    export_df = pd.DataFrame([
        {
            'ticker': p.ticker,
            'entry_date': p.entry_date,
            'entry_price': p.entry_price,
            'quantity': p.quantity,
            'notes': p.notes
        } for p in positions
    ])
    export_df.to_csv("portfolio_export.csv", index=False)
    st.sidebar.success("Exported to portfolio_export.csv")

try:
    # Get current portfolio
    current_portfolio = db.get_portfolio(st.session_state.current_portfolio_id) if st.session_state.current_portfolio_id else None
    
    # Portfolio selector in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("Current Portfolio")
    
    if current_portfolio:
        st.sidebar.markdown(f"**{current_portfolio.name}**")
        if current_portfolio.description:
            st.sidebar.caption(current_portfolio.description)
    
    # Load all portfolios for selector
    all_portfolios = db.get_all_portfolios()
    portfolio_names = [p.name for p in all_portfolios]
    current_portfolio_idx = next((i for i, p in enumerate(all_portfolios) if p.id == st.session_state.current_portfolio_id), 0)
    
    selected_portfolio_name = st.sidebar.selectbox(
        "Switch Portfolio",
        portfolio_names,
        index=current_portfolio_idx,
        key="portfolio_selector"
    )
    
    # Update current portfolio if changed
    if selected_portfolio_name != (current_portfolio.name if current_portfolio else None):
        selected_portfolio = next((p for p in all_portfolios if p.name == selected_portfolio_name), None)
        if selected_portfolio:
            st.session_state.current_portfolio_id = selected_portfolio.id
            st.rerun()
    
    # Initialize or update portfolio data in session state
    if 'portfolio_data' not in st.session_state:
        st.session_state.portfolio_data = {}
    
    # Load portfolio data if we have a current portfolio
    portfolio_data = []
    if current_portfolio:
        # Get portfolio data from session state or refresh if needed
        if str(current_portfolio.id) not in st.session_state.portfolio_data:
            st.session_state.portfolio_data[str(current_portfolio.id)] = refresh_portfolio_data(current_portfolio.id)
        portfolio_data = st.session_state.portfolio_data[str(current_portfolio.id)]

    # Portfolio Overview Page
    if page == "Portfolios":
        st.title("Portfolio Management")
        
        # Create new portfolio
        with st.expander("Create New Portfolio", expanded=False):
            with st.form("create_portfolio_form"):
                col1, col2 = st.columns([2, 1])
                name = col1.text_input("Portfolio Name", key="new_portfolio_name")
                is_default = col2.checkbox("Set as default", value=False, key="new_portfolio_default")
                description = st.text_area("Description", key="new_portfolio_desc")
                
                if st.form_submit_button("Create Portfolio"):
                    if name:
                        try:
                            db = DatabaseManager()
                            db.create_portfolio(
                                name=name,
                                description=description if description else None,
                                is_default=is_default
                            )
                            st.success(f"Portfolio '{name}' created successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating portfolio: {str(e)}")
                    else:
                        st.error("Portfolio name is required")
        
        # List all portfolios
        st.subheader("Your Portfolios")
        portfolios = db.get_all_portfolios()
        
        if not portfolios:
            st.info("No portfolios found. Create your first portfolio above.")
        else:
            for portfolio in portfolios:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    col1.markdown(f"### {portfolio.name}")
                    if portfolio.is_default:
                        col1.caption("⭐ Default Portfolio")
                    if portfolio.description:
                        col1.caption(portfolio.description)
                    
                    # Show basic stats
                    positions = db.get_portfolio_positions(portfolio.id)
                    num_positions = len(positions)
                    total_value = sum(p.quantity * (db.get_market_data(p.id).current_price if db.get_market_data(p.id) else 0) for p in positions)
                    
                    col2.metric("Positions", num_positions)
                    col3.metric("Total Value", f"${total_value:,.2f}" if total_value > 0 else "N/A")
                    
                    # Action buttons
                    with st.expander("Actions"):
                        action_col1, action_col2, action_col3 = st.columns(3)
                        
                        # Set as default
                        if not portfolio.is_default:
                            if action_col1.button("Set as Default", key=f"set_default_{portfolio.id}"):
                                try:
                                    db.update_portfolio(portfolio.id, is_default=True)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating portfolio: {str(e)}")
                        
                        # Edit button
                        if action_col2.button("Edit", key=f"edit_{portfolio.id}"):
                            with st.form(f"edit_form_{portfolio.id}"):
                                new_name = st.text_input("Name", value=portfolio.name)
                                new_desc = st.text_area("Description", value=portfolio.description or "")
                                new_default = st.checkbox("Default Portfolio", value=portfolio.is_default)
                                
                                if st.form_submit_button("Save Changes"):
                                    try:
                                        db.update_portfolio(
                                            portfolio_id=portfolio.id,
                                            name=new_name,
                                            description=new_desc if new_desc else None,
                                            is_default=new_default
                                        )
                                        st.success("Portfolio updated successfully!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error updating portfolio: {str(e)}")
                        
                        # Delete button
                        if action_col3.button("Delete", key=f"delete_{portfolio.id}"):
                            if num_positions > 0:
                                st.warning("Cannot delete a portfolio with positions. Please remove all positions first.")
                            else:
                                try:
                                    db.delete_portfolio(portfolio.id)
                                    st.success("Portfolio deleted successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting portfolio: {str(e)}")
                    
                    st.markdown("---")
    
    elif page == "Portfolio Overview":
        st.title("Portfolio Overview")
        
        if not current_portfolio:
            st.warning("Please select a portfolio first from the sidebar.")
            st.stop()
            
        # Get positions directly from database
        positions = db.get_portfolio_positions(current_portfolio.id)
        
        if not positions:
            st.info("Your portfolio is empty. Go to the Position Management page to add your first position.")
            st.stop()
            
        # Add a refresh button
        refresh = st.button("🔄 Refresh Market Data")
        
        # Create metrics columns for key statistics
        col1, col2, col3, col4 = st.columns(4)
        
        # Portfolio Statistics
        with st.spinner('Loading portfolio metrics...'):
            # Prepare portfolio data
            portfolio_data = []
            for position in positions:
                market_data = db.get_market_data(position.id)
                current_price = market_data.current_price if market_data else None
                cost_basis = position.quantity * position.entry_price
                market_value = position.quantity * current_price if current_price else None
                gain_loss = market_value - cost_basis if market_value is not None else None
                gain_loss_pct = (gain_loss / cost_basis * 100) if gain_loss is not None and cost_basis != 0 else None
                
                portfolio_data.append({
                    'id': position.id,
                    'ticker': position.ticker,
                    'quantity': position.quantity,
                    'entry_price': position.entry_price,
                    'current_price': current_price,
                    'cost_basis': cost_basis,
                    'market_value': market_value,
                    'gain_loss': gain_loss,
                    'gain_loss_pct': gain_loss_pct,
                    'sector': getattr(market_data, 'sector', 'N/A') if market_data else 'N/A',
                    'notes': position.notes or ''
                })
            
            portfolio_view = pd.DataFrame(portfolio_data)
            
            # If refresh button is clicked, fetch new data and update DB
            if refresh:
                for idx, position in enumerate(positions):
                    stock_data = fetch_stock_data_with_feedback(collector, position.ticker, position.id, force_refresh=True)
                    if stock_data and 'current_price' in stock_data:
                        # The fetch_stock_data_with_feedback function already updates the database
                        # So we just need to update our local view
                        market_data = db.get_market_data(position.id)
                        if market_data:
                            portfolio_data[idx]['current_price'] = market_data.current_price
                            portfolio_data[idx]['market_value'] = position.quantity * market_data.current_price
                            portfolio_data[idx]['gain_loss'] = portfolio_data[idx]['market_value'] - portfolio_data[idx]['cost_basis']
                            portfolio_data[idx]['gain_loss_pct'] = (portfolio_data[idx]['gain_loss'] / portfolio_data[idx]['cost_basis'] * 100) \
                                if portfolio_data[idx]['cost_basis'] != 0 else 0
                            portfolio_data[idx]['sector'] = getattr(market_data, 'sector', 'N/A')
                
                portfolio_view = pd.DataFrame(portfolio_data)
                st.success("Market data refreshed! (Values shown are now up to date)")
            
            # Calculate metrics
            total_value = portfolio_view['market_value'].sum() if 'market_value' in portfolio_view.columns else 0
            total_invested = portfolio_view['cost_basis'].sum() if 'cost_basis' in portfolio_view.columns else 0
            total_gain_loss = total_value - total_invested
            total_gain_loss_pct = (total_gain_loss / total_invested * 100) if total_invested != 0 else 0
            
            # Display metrics
            with col1:
                st.metric("Total Value", f"${total_value:,.2f}" if total_value > 0 else "N/A")
            with col2:
                st.metric("Total Invested", f"${total_invested:,.2f}" if total_invested > 0 else "N/A")
            with col3:
                st.metric("Total P/L", 
                         f"${total_gain_loss:,.2f}" if total_gain_loss is not None else "N/A", 
                         f"{total_gain_loss_pct:.2f}%" if total_gain_loss_pct is not None else "N/A",
                         delta_color="normal")
            with col4:
                st.metric("Positions", str(len(positions)))
            
            # Portfolio Table with Sorting
            st.subheader("Holdings")
            display_columns = {
                'ticker': 'Ticker',
                'quantity': 'Quantity',
                'entry_price': 'Avg Cost',
                'current_price': 'Current Price',
                'cost_basis': 'Cost Basis',
                'market_value': 'Market Value',
                'gain_loss': 'Gain/Loss',
                'gain_loss_pct': 'Return %',
                'sector': 'Sector'
            }
            
            display_df = portfolio_view[list(display_columns.keys())].copy()
            display_df = display_df.rename(columns=display_columns)
            display_df = display_df.round(2)
            
            st.dataframe(
                display_df,
                column_config={
                    "Market Value": st.column_config.NumberColumn(
                        "Market Value",
                        format="$%.2f"
                    ),
                    "Gain/Loss": st.column_config.NumberColumn(
                        "Gain/Loss",
                        format="$%.2f"
                    ),
                    "Return %": st.column_config.NumberColumn(
                        "Return %", format="%.2f%%"
                    ),
                    "Cost Basis": st.column_config.NumberColumn(
                        "Cost Basis", format="$%.2f"
                    ),
                    "Current Price": st.column_config.NumberColumn(
                        "Current Price", format="$%.2f"
                    )
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Portfolio Visualizations
            if not portfolio_view.empty and 'market_value' in portfolio_view.columns and not portfolio_view['market_value'].isna().all():
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Portfolio Composition")
                    composition_chart = analyzer.create_portfolio_composition_chart(portfolio_view.rename(columns={
                        'ticker': 'Ticker',
                        'market_value': 'Market Value',
                        'sector': 'Sector'
                    }))
                    if composition_chart:
                        st.plotly_chart(composition_chart, use_container_width=True)
                    else:
                        st.info("Unable to create composition chart. Some market data may be unavailable.")
                
                with col2:
                    st.subheader("Performance by Position")
                    performance_chart = analyzer.create_portfolio_performance_chart(portfolio_view.rename(columns={
                        'ticker': 'Ticker',
                        'gain_loss_pct': 'Return %',
                        'market_value': 'Market Value'
                    }))
                    if performance_chart:
                        st.plotly_chart(performance_chart, use_container_width=True)
                    else:
                        st.info("Unable to create performance chart. Some market data may be unavailable.")
            else:
                st.warning("Unable to create portfolio visualizations. Market data is currently unavailable.")

    elif page == "Individual Stock View":
        st.title("Stock Analysis")
        
        # Get positions directly from database
        positions = db.get_portfolio_positions(current_portfolio.id) if current_portfolio else []
        
        if not positions:
            st.info("Your portfolio is empty. Go to the Position Management page to add your first position.")
            st.stop()
            
        # Get unique tickers from positions
        tickers = list(set([position.ticker for position in positions]))
        
        selected_ticker = st.selectbox(
            "Select Stock",
            options=tickers
        )
        
        if selected_ticker:
            # Get all positions for the selected ticker
            ticker_positions = [p for p in positions if p.ticker == selected_ticker]
            
            # For now, just take the first position if there are multiple
            position = ticker_positions[0] if ticker_positions else None
            
            if not position:
                st.error(f"No position found for {selected_ticker}")
                st.stop()
            
            # Get market data
            market_data = db.get_market_data(position.id)
            stock_data = None
            if market_data:
                stock_data = {c.name: getattr(market_data, c.name) for c in market_data.__table__.columns}
            
            # Manual refresh button
            if st.button("🔄 Refresh Market Data", key=f"refresh_market_{selected_ticker}"):
                stock_data = fetch_stock_data_with_feedback(collector, selected_ticker, position.id, force_refresh=True)
                st.success("Market data refreshed!")
                st.rerun()
            
            # Stock Info Header
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.subheader(f"{selected_ticker} Analysis")
            with col2:
                if stock_data and 'current_price' in stock_data and stock_data['current_price'] is not None:
                    pnl_pct = ((stock_data['current_price'] / position.entry_price) - 1) * 100 if position.entry_price else 0
                    st.metric(
                        "Current Price",
                        f"${stock_data['current_price']:.2f}",
                        f"{pnl_pct:.1f}%"
                    )
            with col3:
                pass  # Remove duplicate refresh button
            
            # Technical Analysis
            col1, col2 = st.columns([6, 1])
            with col1:
                st.subheader("Technical Analysis")
            with col2:
                if st.button("🔄 Refresh Chart", key=f"refresh_chart_{selected_ticker}"):
                    st.session_state[f'hist_data_{selected_ticker}'] = None
                    st.rerun()
            
            # Add time range selector using buttons
            st.write("Time Range:")
            time_range_cols = st.columns(8)
            time_ranges = ['1D', '5D', '1M', '6M', 'YTD', '1Y', '5Y', 'ALL']
            
            # Initialize session state for time range if not exists
            if f'time_range_{selected_ticker}' not in st.session_state:
                st.session_state[f'time_range_{selected_ticker}'] = '1Y'
            
            # Create a button for each time range
            for i, time_range in enumerate(time_ranges):
                with time_range_cols[i]:
                    if st.button(
                        time_range,
                        key=f"btn_time_range_{selected_ticker}_{time_range}",
                        type="secondary" if st.session_state[f'time_range_{selected_ticker}'] != time_range else "primary"
                    ):
                        st.session_state[f'time_range_{selected_ticker}'] = time_range
                        st.rerun()
            
            selected_time_range = st.session_state[f'time_range_{selected_ticker}']
            
            # Add indicator selection
            st.sidebar.header("Chart Options")
            show_options = {
                'candlesticks': st.sidebar.checkbox("Show Candlesticks", value=True, key=f"show_candles_{selected_ticker}"),
                'bollinger': st.sidebar.checkbox("Show Bollinger Bands", value=True, key=f"show_bb_{selected_ticker}"),
                'sma': st.sidebar.checkbox("Show Moving Averages", value=True, key=f"show_sma_{selected_ticker}"),
                'rsi': st.sidebar.checkbox("Show RSI", value=True, key=f"show_rsi_{selected_ticker}"),
                'volume': st.sidebar.checkbox("Show Volume", value=True, key=f"show_volume_{selected_ticker}")
            }
            
            # Use session state to store historical data
            if f'hist_data_{selected_ticker}' not in st.session_state:
                st.session_state[f'hist_data_{selected_ticker}'] = fetch_historical_data_with_feedback(collector, selected_ticker)
            
            hist_data = st.session_state[f'hist_data_{selected_ticker}']
            if hist_data is not None and not hist_data.empty:
                tech_chart = analyzer.create_technical_chart(hist_data, selected_ticker, show_options, selected_time_range)
                if tech_chart:
                    st.plotly_chart(tech_chart, use_container_width=True)
            
            # Technical Indicators
            st.subheader("Technical Indicators")
            col1, col2 = st.columns([6, 1])
            with col2:
                if st.button("🔄 Refresh Indicators", key=f"refresh_tech_{selected_ticker}"):
                    technical_data = fetch_technical_data_with_feedback(collector, selected_ticker, position.id)
                    if technical_data:
                        st.session_state[f'tech_data_{selected_ticker}'] = technical_data
                        st.rerun()
            
            if f'tech_data_{selected_ticker}' in st.session_state:
                technical_data = st.session_state[f'tech_data_{selected_ticker}']
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("RSI", f"{technical_data.get('rsi', 'N/A')}")
                with col2:
                    st.metric("MACD", f"{technical_data.get('macd', 'N/A'):.2f}" if 'macd' in technical_data else "N/A")
                with col3:
                    st.metric("Signal", f"{technical_data.get('macd_signal', 'N/A'):.2f}" if 'macd_signal' in technical_data else "N/A")
            
            # Fundamentals and Market Data
            if stock_data:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.subheader("Market Data")
                    st.write(f"Day Range: ${stock_data.get('day_low', 0):.2f} - ${stock_data.get('day_high', 0):.2f}" if 'day_low' in stock_data and 'day_high' in stock_data else "Day Range: N/A")
                    st.write(f"52W Range: ${stock_data.get('fifty_two_week_low', 0):.2f} - ${stock_data.get('fifty_two_week_high', 0):.2f}" if 'fifty_two_week_low' in stock_data and 'fifty_two_week_high' in stock_data else "52W Range: N/A")
                    st.write(f"Volume: {format_large_number(stock_data.get('volume'))}" if 'volume' in stock_data else "Volume: N/A")
                
                with col2:
                    st.subheader("Fundamentals")
                    st.write(f"P/E Ratio: {stock_data.get('pe_ratio', 'N/A'):.2f}" if stock_data.get('pe_ratio') is not None else "P/E Ratio: N/A")
                    st.write(f"EPS: ${stock_data.get('eps', 'N/A'):.2f}" if stock_data.get('eps') is not None else "EPS: N/A")
                    st.write(f"Market Cap: {format_large_number(stock_data.get('market_cap'))}" if 'market_cap' in stock_data else "Market Cap: N/A")
                
                with col3:
                    st.subheader("Position Details")
                    st.write(f"Shares: {position.quantity}")
                    st.write(f"Entry Price: ${position.entry_price:.2f}")
                    st.write(f"Entry Date: {position.entry_date.strftime('%Y-%m-%d')}" if hasattr(position, 'entry_date') and position.entry_date else "Entry Date: N/A")

    elif page == "Technical Alerts":
        st.title("Technical Alerts")
        
        # Get positions directly from database
        positions = db.get_portfolio_positions(current_portfolio.id) if current_portfolio else []
        
        if not positions:
            st.info("Your portfolio is empty. Go to the Position Management page to add your first position.")
            st.stop()
            
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("🔄 Refresh All Alerts"):
                with st.spinner("Refreshing technical data..."):
                    for position in positions:
                        technical_data = fetch_technical_data_with_feedback(collector, position.ticker, position.id)
                        if technical_data:
                            st.session_state[f'tech_data_{position.ticker}'] = technical_data
                st.success("Technical alerts refreshed!")
                st.rerun()
        
        alerts = []
        with st.spinner("Analyzing positions for technical signals..."):
            for position in positions:
                ticker = position.ticker
                
                # Get technical data from session state or database
                if f'tech_data_{ticker}' not in st.session_state:
                    # Try to load from database if available
                    market_data = db.get_market_data(position.id)
                    if market_data and hasattr(market_data, 'rsi') and market_data.rsi is not None:
                        st.session_state[f'tech_data_{ticker}'] = {
                            'rsi': getattr(market_data, 'rsi', None),
                            'macd': getattr(market_data, 'macd', None),
                            'macd_signal': getattr(market_data, 'macd_signal', None),
                            'rsi_overbought': getattr(market_data, 'rsi_overbought', False),
                            'rsi_oversold': getattr(market_data, 'rsi_oversold', False),
                            'macd_crossover': getattr(market_data, 'macd_crossover', False),
                            'is_above_50_sma': getattr(market_data, 'is_above_50_sma', False),
                            'is_above_200_sma': getattr(market_data, 'is_above_200_sma', False)
                        }
                    else:
                        continue
                
                technical_data = st.session_state[f'tech_data_{ticker}']
                
                if technical_data:
                    # RSI Alerts
                    if technical_data.get('rsi_overbought'):
                        alerts.append({
                            'ticker': ticker,
                            'signal': "RSI Overbought",
                            'value': f"RSI: {technical_data.get('rsi', 'N/A')}",
                            'type': 'warning'
                        })
                    elif technical_data.get('rsi_oversold'):
                        alerts.append({
                            'ticker': ticker,
                            'signal': "RSI Oversold",
                            'value': f"RSI: {technical_data.get('rsi', 'N/A')}",
                            'type': 'opportunity'
                        })
                    
                    # MACD Alerts
                    if technical_data.get('macd_crossover'):
                        alerts.append({
                            'ticker': ticker,
                            'signal': "Bullish MACD Crossover",
                            'value': f"MACD: {technical_data.get('macd', 'N/A'):.2f}",
                            'type': 'opportunity'
                        })
                    
                    # Moving Average Alerts
                    if technical_data.get('is_above_200_sma') and not technical_data.get('is_above_50_sma'):
                        alerts.append({
                            'ticker': ticker,
                            'signal': "50 SMA Bearish Cross",
                            'value': "Price below 50 SMA",
                            'type': 'warning'
                        })
                    elif not technical_data.get('is_above_200_sma') and technical_data.get('is_above_50_sma'):
                        alerts.append({
                            'ticker': ticker,
                            'signal': "50 SMA Bullish Cross",
                            'value': "Price above 50 SMA",
                            'type': 'opportunity'
                        })
        
        if alerts:
            # Sort alerts by ticker for better readability
            alerts.sort(key=lambda x: x['ticker'])
            
            # Group alerts by type for better organization
            warning_alerts = [a for a in alerts if a['type'] == 'warning']
            opportunity_alerts = [a for a in alerts if a['type'] == 'opportunity']
            
            # Display warnings first
            if warning_alerts:
                st.subheader("⚠️ Warnings")
                for alert in warning_alerts:
                    st.warning(f"{alert['ticker']}: {alert['signal']} ({alert['value']})")
            
            # Then display opportunities
            if opportunity_alerts:
                st.subheader("✅ Opportunities")
                for alert in opportunity_alerts:
                    st.success(f"{alert['ticker']}: {alert['signal']} ({alert['value']})")
        else:
            st.info("No technical alerts at this time.")
            
            # Show help text about how to generate alerts
            st.info(
                "To see technical alerts, make sure you have positions in your portfolio "
                "and click the 'Refresh All Alerts' button to fetch the latest technical data."
            )

    elif page == "Position Management":
        if not current_portfolio:
            st.warning("Please select or create a portfolio first from the Portfolios page.")
            st.stop()
        
        st.title(f"Position Management - {current_portfolio.name}")
        
        # Get positions directly from database
        positions = db.get_portfolio_positions(current_portfolio.id)
        st.write(f"Number of positions: {len(positions) if positions else 0}")
        
        # Add new position form
        st.subheader("Add New Position")
        with st.form("add_position"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                ticker = st.text_input("Ticker Symbol").upper()
                entry_date = st.date_input("Entry Date", datetime.today())
            
            with col2:
                entry_price = st.number_input("Entry Price", min_value=0.01, step=0.01)
                quantity = st.number_input("Quantity", min_value=1, step=1)
            
            with col3:
                notes = st.text_area("Notes")
            
            submitted = st.form_submit_button("Add Position")
            
            if submitted and ticker and entry_price and quantity:
                try:
                    # Add the new position to the database
                    db.add_position(
                        portfolio_id=current_portfolio.id,
                        ticker=ticker,
                        entry_date=entry_date,
                        entry_price=entry_price,
                        quantity=quantity,
                        notes=notes
                    )
                    # Refresh market data for the new position
                    position = db.get_portfolio_positions(current_portfolio.id)[-1]  # Get the newly added position
                    collector.get_stock_data(ticker, position.id)
                    st.success(f"Added {ticker} position to portfolio!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding position: {str(e)}")

        # Manage existing positions
        st.subheader("Manage Positions")
        if positions:
            for position in positions:
                # Get market data for the position
                market_data = db.get_market_data(position.id)
                current_price = market_data.current_price if market_data else 0
                current_value = position.quantity * current_price
                cost_basis = position.quantity * position.entry_price
                pnl = current_value - cost_basis
                pnl_pct = (pnl / cost_basis * 100) if cost_basis != 0 else 0
                
                with st.expander(f"📈 {position.ticker} - {position.quantity} shares"):
                    col1, col2 = st.columns(2)
                    
                    # Position details
                    with col1:
                        st.subheader("Position Details")
                        st.write(f"Ticker: {position.ticker}")
                        st.write(f"Entry Price: ${position.entry_price:.2f}")
                        st.write(f"Current Price: ${current_price:.2f}" if current_price else "Current Price: N/A")
                        st.write(f"Quantity: {position.quantity}")
                        st.write(f"Cost Basis: ${cost_basis:.2f}")
                        st.write(f"Current Value: ${current_value:.2f}" if current_price else "")
                        st.write(f"P/L: ${pnl:,.2f} ({pnl_pct:.2f}%)" if current_price else "")
                        
                        if position.notes:
                            st.write("---")
                            st.write("**Notes:**")
                            st.write(position.notes)
                    
                    # Edit form
                    with col2:
                        with st.form(f"edit_form_{position.id}"):
                            st.subheader("Edit Position")
                            new_price = st.number_input(
                                "Entry Price", 
                                value=float(position.entry_price), 
                                key=f"price_{position.id}",
                                step=0.01
                            )
                            new_quantity = st.number_input(
                                "Quantity", 
                                value=int(position.quantity), 
                                key=f"qty_{position.id}",
                                step=1,
                                min_value=1
                            )
                            new_notes = st.text_area(
                                "Notes", 
                                value=position.notes or '', 
                                key=f"notes_{position.id}",
                                height=100
                            )
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("💾 Update"):
                                    try:
                                        db.update_position(
                                            position_id=position.id,
                                            entry_price=new_price,
                                            quantity=new_quantity,
                                            notes=new_notes if new_notes.strip() else None
                                        )
                                        st.success("Position updated!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error updating position: {str(e)}")
                            
                            with col2:
                                delete_clicked = st.form_submit_button("🗑️ Delete")
                                if delete_clicked:
                                    if f'confirm_delete_{position.id}' not in st.session_state:
                                        st.session_state[f'confirm_delete_{position.id}'] = True
                                        st.rerun()
                                    else:
                                        try:
                                            if db.delete_position(position.id):
                                                # Clear any related cache
                                                for key in list(st.session_state.keys()):
                                                    if key.startswith('tech_data_') or key.startswith('hist_data_'):
                                                        del st.session_state[key]
                                                st.success("Position deleted successfully!")
                                                if f'confirm_delete_{position.id}' in st.session_state:
                                                    del st.session_state[f'confirm_delete_{position.id}']
                                                st.rerun()
                                            else:
                                                st.error("Failed to delete position. Please try again.")
                                        except Exception as e:
                                            st.error(f"Error deleting position: {str(e)}")
                                            logger.error(f"Error deleting position {position.id}: {str(e)}")
                                        finally:
                                            if f'confirm_delete_{position.id}' in st.session_state:
                                                del st.session_state[f'confirm_delete_{position.id}']
                            
                            # Show confirmation message if needed
                            if st.session_state.get(f'confirm_delete_{position.id}', False):
                                st.warning("Are you sure you want to delete this position? This action cannot be undone.")
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.form_submit_button("✅ Confirm Delete"):
                                        try:
                                            if db.delete_position(position.id):
                                                # Clear any related cache
                                                for key in list(st.session_state.keys()):
                                                    if key.startswith('tech_data_') or key.startswith('hist_data_'):
                                                        del st.session_state[key]
                                                st.success("Position deleted successfully!")
                                                if f'confirm_delete_{position.id}' in st.session_state:
                                                    del st.session_state[f'confirm_delete_{position.id}']
                                                st.rerun()
                                            else:
                                                st.error("Failed to delete position. Please try again.")
                                        except Exception as e:
                                            st.error(f"Error deleting position: {str(e)}")
                                            logger.error(f"Error deleting position {position.id}: {str(e)}")
                                with col2:
                                    if st.form_submit_button("❌ Cancel"):
                                        if f'confirm_delete_{position.id}' in st.session_state:
                                            del st.session_state[f'confirm_delete_{position.id}']
                                        st.rerun()
        else:
            st.info("No positions found in this portfolio. Add your first position using the form above.")

    elif page == "AI Export page":
        st.title("AI Analysis Export")
        
        if not df.empty:
            export_type = st.radio(
                "Select Export Type",
                ["Single Stock", "Entire Portfolio"],
                horizontal=True
            )
            
            if export_type == "Single Stock":
                col1, col2 = st.columns([3, 1])
                with col1:
                    selected_ticker = st.selectbox(
                        "Select Stock to Analyze",
                        options=df['ticker'].unique(),
                        key="yaml_ticker_select"
                    )
                with col2:
                    st.write("")  # Add some spacing
                    st.write("")  # Add some spacing
                    export_button = st.button("🔄 Generate YAML", key="generate_single_stock")
                
                if selected_ticker and export_button:
                    position = df[df['ticker'] == selected_ticker].iloc[0]
                    logger.info(f"Generating YAML for {selected_ticker} with position ID: {position['id']}")
                    
                    with st.spinner(f"Generating analysis for {selected_ticker}..."):
                        yaml_data = yaml_exporter.generate_stock_yaml(selected_ticker, position['id'])
                        
                    if yaml_data:
                        yaml_dict = yaml.safe_load(yaml_data)
                        logger.info(f"Generated YAML data: {yaml_dict}")
                        
                        # Show appropriate status message based on data availability
                        if yaml_dict['data_availability'] == 'partial':
                            st.warning("⚠️ Only basic position data is available. Market data could not be fetched.")
                        elif 'data_timestamp' in yaml_dict:
                            data_time = datetime.strptime(yaml_dict['data_timestamp'], '%Y-%m-%d %H:%M:%S')
                            time_diff = datetime.now() - data_time
                            if time_diff > timedelta(minutes=15):
                                st.info(f"⚠️ Using cached market data from {yaml_dict['data_timestamp']}. Some information may not be current.")
                        
                        # Create a container for the YAML output and buttons
                        yaml_container = st.container()
                        col1, col2 = st.columns([3, 1])
                        
                        with yaml_container:
                            st.code(yaml_data, language="yaml")
                        
                        with col1:
                            st.download_button(
                                "💾 Download YAML",
                                yaml_data,
                                file_name=f"{selected_ticker}_analysis.yaml",
                                mime="text/yaml",
                                key="download_single_stock"
                            )
                        
                        with col2:
                            if st.button("📋 Copy to Clipboard", key="copy_single_stock"):
                                try:
                                    pd.DataFrame([yaml_data]).to_clipboard(index=False, header=False)
                                    st.success("Copied to clipboard!")
                                except:
                                    st.error("Could not copy to clipboard. Please copy manually.")
            
            else:  # Entire Portfolio
                col1, col2 = st.columns([3, 1])
                with col2:
                    st.write("")  # Add some spacing
                    st.write("")  # Add some spacing
                    export_button = st.button("🔄 Generate Portfolio YAML", key="generate_portfolio")
                
                if export_button:
                    with st.spinner("Generating portfolio analysis..."):
                        portfolio_yaml = yaml_exporter.export_portfolio_yaml(df)
                        
                    if portfolio_yaml:
                        yaml_dict = yaml.safe_load(portfolio_yaml)
                        
                        # Check data availability for all positions
                        partial_data_positions = []
                        cached_data_positions = []
                        oldest_data = None
                        
                        for ticker, position_data in yaml_dict['positions'].items():
                            if position_data['data_availability'] == 'partial':
                                partial_data_positions.append(ticker)
                            elif position_data['data_availability'] == 'full':
                                data_time = datetime.strptime(position_data['data_timestamp'], '%Y-%m-%d %H:%M:%S')
                                time_diff = datetime.now() - data_time
                                if time_diff > timedelta(minutes=15):
                                    cached_data_positions.append(ticker)
                                    if not oldest_data or data_time < oldest_data:
                                        oldest_data = data_time
                        
                        # Show appropriate status messages
                        if partial_data_positions:
                            st.warning(f"⚠️ Only basic position data available for: {', '.join(partial_data_positions)}")
                        if cached_data_positions:
                            st.info(f"⚠️ Using cached market data for: {', '.join(cached_data_positions)} (oldest from {oldest_data.strftime('%Y-%m-%d %H:%M:%S')})")
                        
                        # Create a container for the YAML output and buttons
                        yaml_container = st.container()
                        col1, col2 = st.columns([3, 1])
                        
                        with yaml_container:
                            st.code(portfolio_yaml, language="yaml")
                        
                        with col1:
                            st.download_button(
                                "💾 Download Portfolio YAML",
                                portfolio_yaml,
                                file_name="portfolio_analysis.yaml",
                                mime="text/yaml",
                                key="download_portfolio"
                            )
                        
                        with col2:
                            if st.button("📋 Copy to Clipboard", key="copy_portfolio"):
                                try:
                                    pd.DataFrame([portfolio_yaml]).to_clipboard(index=False, header=False)
                                    st.success("Copied to clipboard!")
                                except:
                                    st.error("Could not copy to clipboard. Please copy manually.")
                        
                        st.markdown("### 🤖 Portfolio Analysis Prompt")
                        data_status = []
                        if partial_data_positions:
                            data_status.append(f"- Basic position data only for: {', '.join(partial_data_positions)}")
                        if cached_data_positions:
                            data_status.append(f"- Using cached data for: {', '.join(cached_data_positions)} (oldest: {oldest_data.strftime('%Y-%m-%d %H:%M:%S')})")
                        
                        prompt = f"""Analyze this portfolio data and provide insights on:
1. Overall portfolio health and diversification
2. Key risks and opportunities across positions
3. Suggested portfolio adjustments
4. Individual position recommendations

Data availability notes:
{chr(10).join(data_status) if data_status else "All data is current"}"""
                        
                        st.code(prompt, language="markdown")
                    else:
                        st.error("Unable to generate portfolio analysis. Please check your database connection.")

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.info("Please try refreshing the page. If the error persists, check your database connection.")