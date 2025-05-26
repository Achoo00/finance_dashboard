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

# Configure Streamlit page
st.set_page_config(
    page_title="Portfolio Manager",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Initialize the data collector and database manager
@st.cache_resource
def get_data_collector():
    return StockDataCollector()

@st.cache_resource
def get_database_manager():
    return DatabaseManager()

@st.cache_resource
def get_yaml_exporter():
    return StockDataYAMLExporter()

collector = get_data_collector()
db = get_database_manager()
analyzer = PortfolioAnalyzer()
yaml_exporter = get_yaml_exporter()

def format_large_number(num):
    if num is None:
        return "N/A"
    if num >= 1_000_000_000:
        return f"${num/1_000_000_000:.2f}B"
    if num >= 1_000_000:
        return f"${num/1_000_000:.2f}M"
    return f"${num:,.2f}"

# Add error handling for data fetching
def fetch_stock_data_with_feedback(collector, ticker, position_id):
    with st.spinner(f'Fetching data for {ticker}...'):
        data = collector.get_stock_data(ticker, position_id)
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

# Navigation
page = st.sidebar.radio(
    "",  # Remove label
    ["Portfolio Overview", "Individual Stock View", "Technical Alerts", "Position Management", "AI Export"],
    key="navigation"
)

try:
    # Load portfolio data
    positions = db.get_all_positions()
    portfolio_data = []
    for position in positions:
        portfolio_data.append({
            'id': position.id,
            'ticker': position.ticker,
            'entry_date': position.entry_date,
            'entry_price': position.entry_price,
            'quantity': position.quantity,
            'notes': position.notes
        })
    df = pd.DataFrame(portfolio_data)

    # Portfolio Overview Page
    if page == "Portfolio Overview":
        st.title("Portfolio Overview")
        
        if df.empty:
            st.info("Your portfolio is empty. Go to the Position Management page to add your first position.")
        else:
            # Create metrics columns for key statistics
            col1, col2, col3, col4 = st.columns(4)
            
            # Portfolio Statistics
            with st.spinner('Loading portfolio metrics...'):
                portfolio_view = df.copy()
                portfolio_view['Current Price'] = None
                portfolio_view['Market Value'] = None
                portfolio_view['Gain/Loss'] = None
                portfolio_view['Gain/Loss %'] = None
                
                for idx, row in df.iterrows():
                    stock_data = fetch_stock_data_with_feedback(collector, row['ticker'], row['id'])
                    
                    if stock_data and stock_data.get('current_price'):
                        current_price = stock_data['current_price']
                        portfolio_view.loc[idx, 'Current Price'] = current_price
                        market_value = current_price * row['quantity']  # Calculate market value based on position size
                        cost_basis = row['entry_price'] * row['quantity']
                        portfolio_view.loc[idx, 'Market Value'] = market_value
                        portfolio_view.loc[idx, 'Gain/Loss'] = market_value - cost_basis
                        portfolio_view.loc[idx, 'Gain/Loss %'] = ((market_value / cost_basis) - 1) * 100
                    else:
                        st.warning(f"Could not fetch current price for {row['ticker']}")
                
                # Calculate metrics only if we have market values
                if not portfolio_view['Market Value'].isnull().all():
                    metrics = analyzer.calculate_portfolio_metrics(portfolio_view)
                    
                    with col1:
                        st.metric("Total Value", f"${metrics['Total Value']:,.2f}")
                    with col2:
                        st.metric("Total Gain/Loss", f"${metrics['Total Gain/Loss']:,.2f}")
                    with col3:
                        st.metric("Return", f"{metrics['Return (%)']:.2f}%")
                    with col4:
                        st.metric("Positions", str(metrics['Number of Positions']))
                else:
                    st.error("Unable to fetch market data. Please try again later.")

            # Portfolio Table with Sorting
            st.subheader("Holdings")
            sortable_df = portfolio_view.copy()
            sortable_df = sortable_df.round(2)
            st.dataframe(
                sortable_df,
                column_config={
                    "Market Value": st.column_config.NumberColumn(
                        "Market Value",
                        format="$%.2f"
                    ),
                    "Gain/Loss": st.column_config.NumberColumn(
                        "Gain/Loss",
                        format="$%.2f"
                    ),
                    "Gain/Loss %": st.column_config.NumberColumn(
                        "Return %",
                        format="%.2f%%"
                    )
                },
                use_container_width=True
            )

            # Portfolio Visualizations
            if not portfolio_view['Market Value'].isnull().all():
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Portfolio Composition")
                    composition_chart = analyzer.create_portfolio_composition_chart(portfolio_view)
                    if composition_chart:
                        st.plotly_chart(composition_chart, use_container_width=True)
                    else:
                        st.info("Unable to create composition chart. Some market data may be unavailable.")
                
                with col2:
                    st.subheader("Performance by Position")
                    performance_chart = analyzer.create_portfolio_performance_chart(portfolio_view)
                    if performance_chart:
                        st.plotly_chart(performance_chart, use_container_width=True)
                    else:
                        st.info("Unable to create performance chart. Some market data may be unavailable.")
            else:
                st.warning("Unable to create portfolio visualizations. Market data is currently unavailable.")

    elif page == "Individual Stock View":
        st.title("Stock Analysis")
        
        if not df.empty:
            selected_ticker = st.selectbox(
                "Select Stock",
                options=df['ticker'].unique()
            )
            
            if selected_ticker:
                position = df[df['ticker'] == selected_ticker].iloc[0]
                
                # Stock Info Header
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.subheader(f"{selected_ticker} Analysis")
                with col2:
                    stock_data = fetch_stock_data_with_feedback(collector, selected_ticker, position['id'])
                    if stock_data and stock_data['current_price']:
                        st.metric(
                            "Current Price",
                            f"${stock_data['current_price']:.2f}",
                            f"{((stock_data['current_price'] / position['entry_price']) - 1) * 100:.1f}%"
                        )
                with col3:
                    if st.button("🔄 Refresh Market Data", key=f"refresh_market_{selected_ticker}"):
                        st.experimental_rerun()
                
                # Technical Analysis
                col1, col2 = st.columns([6, 1])
                with col1:
                    st.subheader("Technical Analysis")
                with col2:
                    if st.button("🔄 Refresh Chart", key=f"refresh_chart_{selected_ticker}"):
                        st.session_state[f'hist_data_{selected_ticker}'] = None
                        st.experimental_rerun()
                
                # Use session state to store historical data
                if f'hist_data_{selected_ticker}' not in st.session_state:
                    st.session_state[f'hist_data_{selected_ticker}'] = fetch_historical_data_with_feedback(collector, selected_ticker)
                
                hist_data = st.session_state[f'hist_data_{selected_ticker}']
                if hist_data is not None and not hist_data.empty:
                    tech_chart = analyzer.create_technical_chart(hist_data, selected_ticker)
                    if tech_chart:
                        st.plotly_chart(tech_chart, use_container_width=True)
                
                # Technical Indicators
                st.subheader("Technical Indicators")
                col1, col2 = st.columns([6, 1])
                with col2:
                    if st.button("🔄 Refresh Indicators", key=f"refresh_tech_{selected_ticker}"):
                        technical_data = fetch_technical_data_with_feedback(collector, selected_ticker, position['id'])
                        if technical_data:
                            st.session_state[f'tech_data_{selected_ticker}'] = technical_data
                            st.experimental_rerun()
                
                if f'tech_data_{selected_ticker}' in st.session_state:
                    technical_data = st.session_state[f'tech_data_{selected_ticker}']
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("RSI", f"{technical_data['rsi']:.1f}")
                    with col2:
                        st.metric("MACD", f"{technical_data['macd']:.2f}")
                    with col3:
                        st.metric("Signal", f"{technical_data['macd_signal']:.2f}")
                
                # Fundamentals and Market Data
                if stock_data:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.subheader("Market Data")
                        st.write(f"Day Range: ${stock_data['day_low']:.2f} - ${stock_data['day_high']:.2f}")
                        st.write(f"52W Range: ${stock_data['fifty_two_week_low']:.2f} - ${stock_data['fifty_two_week_high']:.2f}")
                        st.write(f"Volume: {format_large_number(stock_data['volume'])}")
                    
                    with col2:
                        st.subheader("Fundamentals")
                        st.write(f"P/E Ratio: {stock_data['pe_ratio']:.2f}" if stock_data['pe_ratio'] else "P/E Ratio: N/A")
                        st.write(f"EPS: ${stock_data['eps']:.2f}" if stock_data['eps'] else "EPS: N/A")
                        st.write(f"Market Cap: {format_large_number(stock_data['market_cap'])}")
                    
                    with col3:
                        st.subheader("Position Details")
                        st.write(f"Shares: {position['quantity']}")
                        st.write(f"Entry Price: ${position['entry_price']:.2f}")
                        st.write(f"Entry Date: {position['entry_date'].strftime('%Y-%m-%d')}")

    elif page == "Technical Alerts":
        st.title("Technical Alerts")
        
        if not df.empty:
            col1, col2 = st.columns([6, 1])
            with col2:
                if st.button("🔄 Refresh All Alerts"):
                    for ticker in df['ticker'].unique():
                        if f'tech_data_{ticker}' in st.session_state:
                            del st.session_state[f'tech_data_{ticker}']
                    st.experimental_rerun()
            
            alerts = []
            with st.spinner("Analyzing positions for technical signals..."):
                for _, position in df.iterrows():
                    ticker = position['ticker']
                    
                    # Use session state to store technical data
                    if f'tech_data_{ticker}' not in st.session_state:
                        technical_data = fetch_technical_data_with_feedback(collector, ticker, position['id'])
                        if technical_data:
                            st.session_state[f'tech_data_{ticker}'] = technical_data
                    else:
                        technical_data = st.session_state[f'tech_data_{ticker}']
                    
                    if technical_data:
                        # RSI Alerts
                        if technical_data['rsi_overbought']:
                            alerts.append({
                                'ticker': ticker,
                                'signal': "RSI Overbought",
                                'value': f"RSI: {technical_data['rsi']:.1f}",
                                'type': 'warning'
                            })
                        elif technical_data['rsi_oversold']:
                            alerts.append({
                                'ticker': ticker,
                                'signal': "RSI Oversold",
                                'value': f"RSI: {technical_data['rsi']:.1f}",
                                'type': 'opportunity'
                            })
                        
                        # MACD Alerts
                        if technical_data['macd_crossover']:
                            alerts.append({
                                'ticker': ticker,
                                'signal': "Bullish MACD Crossover",
                                'value': f"MACD: {technical_data['macd']:.2f}",
                                'type': 'opportunity'
                            })
                        
                        # Moving Average Alerts
                        if technical_data['is_above_200_sma'] and not technical_data['is_above_50_sma']:
                            alerts.append({
                                'ticker': ticker,
                                'signal': "50 SMA Bearish Cross",
                                'value': "Price below 50 SMA",
                                'type': 'warning'
                            })
                        elif not technical_data['is_above_200_sma'] and technical_data['is_above_50_sma']:
                            alerts.append({
                                'ticker': ticker,
                                'signal': "50 SMA Bullish Cross",
                                'value': "Price above 50 SMA",
                                'type': 'opportunity'
                            })
            
            if alerts:
                for alert in alerts:
                    if alert['type'] == 'warning':
                        st.warning(f"⚠️ {alert['ticker']}: {alert['signal']} ({alert['value']})")
                    else:
                        st.success(f"✅ {alert['ticker']}: {alert['signal']} ({alert['value']})")
            else:
                st.info("No technical alerts at this time.")

    elif page == "Position Management":
        st.title("Position Management")
        
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
                db.add_position(
                    ticker=ticker,
                    entry_date=entry_date,
                    entry_price=entry_price,
                    quantity=quantity,
                    notes=notes
                )
                st.success(f"Added {ticker} position to portfolio!")
                st.experimental_rerun()

        # Manage existing positions
        st.subheader("Manage Positions")
        if not df.empty:
            for idx, row in df.iterrows():
                with st.expander(f"📈 {row['ticker']} - {row['quantity']} shares"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        stock_data = fetch_stock_data_with_feedback(collector, row['ticker'], row['id'])
                        if stock_data:
                            st.subheader("Current Data")
                            current_price = stock_data['current_price']
                            if current_price:
                                gain_loss = (current_price - row['entry_price']) * row['quantity']
                                gain_loss_pct = ((current_price / row['entry_price']) - 1) * 100
                                st.metric(
                                    "Current Value",
                                    f"${current_price * row['quantity']:,.2f}",
                                    f"{gain_loss_pct:.1f}% (${gain_loss:,.2f})"
                                )
                    
                    with col2:
                        with st.form(f"edit_form_{idx}"):
                            new_price = st.number_input("Update Entry Price", value=float(row['entry_price']), key=f"price_{idx}")
                            new_quantity = st.number_input("Update Quantity", value=int(row['quantity']), key=f"qty_{idx}")
                            new_notes = st.text_input("Update Notes", value=row['notes'], key=f"notes_{idx}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("Update"):
                                    db.update_position(
                                        position_id=row['id'],
                                        entry_price=new_price,
                                        quantity=new_quantity,
                                        notes=new_notes
                                    )
                                    st.success("Position updated!")
                                    st.experimental_rerun()
                            
                            with col2:
                                if st.form_submit_button("Delete", type="primary"):
                                    db.delete_position(row['id'])
                                    st.success("Position deleted!")
                                    st.experimental_rerun()

    else:  # AI Export page
        st.title("AI Analysis Export")
        
        if not df.empty:
            export_type = st.radio(
                "Select Export Type",
                ["Single Stock", "Entire Portfolio"],
                horizontal=True
            )
            
            if export_type == "Single Stock":
                selected_ticker = st.selectbox(
                    "Select Stock to Analyze",
                    options=df['ticker'].unique(),
                    key="yaml_ticker_select"
                )
                
                if selected_ticker:
                    position = df[df['ticker'] == selected_ticker].iloc[0]
                    with st.spinner(f"Generating analysis for {selected_ticker}..."):
                        yaml_data = yaml_exporter.generate_stock_yaml(selected_ticker, position['id'])
                        
                    if yaml_data:
                        st.code(yaml_data, language="yaml")
                        st.download_button(
                            "Download YAML",
                            yaml_data,
                            file_name=f"{selected_ticker}_analysis.yaml",
                            mime="text/yaml"
                        )
                        
                        st.markdown("### 🤖 AI Analysis Prompt")
                        prompt = f"""Analyze this stock data and suggest actions. Focus on:
1. Notable technical signals and their implications
2. Key fundamental metrics and their interpretation
3. Potential risks and opportunities
4. Suggested actions (buy, hold, sell) with reasoning"""
                        
                        st.code(prompt, language="markdown")
                    else:
                        st.error("Unable to generate analysis. Please try again later.")
            
            else:  # Entire Portfolio
                with st.spinner("Generating portfolio analysis..."):
                    portfolio_yaml = yaml_exporter.export_portfolio_yaml(df)
                    
                if portfolio_yaml:
                    st.code(portfolio_yaml, language="yaml")
                    st.download_button(
                        "Download Portfolio YAML",
                        portfolio_yaml,
                        file_name="portfolio_analysis.yaml",
                        mime="text/yaml"
                    )
                    
                    st.markdown("### 🤖 Portfolio Analysis Prompt")
                    prompt = """Analyze this portfolio data and provide insights on:
1. Overall portfolio health and diversification
2. Key risks and opportunities across positions
3. Suggested portfolio adjustments
4. Individual position recommendations"""
                    
                    st.code(prompt, language="markdown")
                else:
                    st.error("Unable to generate portfolio analysis. Please try again later.")

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.info("Please try refreshing the page. If the error persists, check your database connection.") 