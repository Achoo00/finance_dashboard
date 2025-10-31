import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging
import time
from database import DatabaseManager
import json
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockDataCollector:
    def __init__(self):
        self.db = DatabaseManager()
        self.cache_timeout = timedelta(minutes=15)
        self.max_retries = 3
        self.base_delay = 2  # Base delay in seconds
        self.last_request_time = {}  # Dictionary to track last request time per ticker
        self.min_request_interval = 2  # Minimum seconds between requests for the same ticker

    def _is_cache_valid(self, market_data):
        """Check if cached data is still valid"""
        if not market_data or not market_data.last_updated:
            return False
        return datetime.now() - market_data.last_updated < self.cache_timeout

    def _wait_for_rate_limit(self, ticker):
        """Ensure minimum time between requests for the same ticker"""
        if ticker in self.last_request_time:
            elapsed = time.time() - self.last_request_time[ticker]
            if elapsed < self.min_request_interval:
                time.sleep(self.min_request_interval - elapsed + random.uniform(0, 1))
        self.last_request_time[ticker] = time.time()

    def _fetch_with_retry(self, ticker, fetch_func):
        """Generic retry mechanism with exponential backoff"""
        for attempt in range(self.max_retries):
            try:
                self._wait_for_rate_limit(ticker)
                return fetch_func()
            except Exception as e:
                if "429" in str(e):  # Rate limit error
                    delay = (self.base_delay ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Rate limit hit for {ticker}, waiting {delay:.2f} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Error fetching data for {ticker}: {str(e)}")
                    return None
        logger.error(f"Max retries exceeded for {ticker}")
        return None

    def _convert_cached_data_to_dict(self, cached_data):
        """Convert cached MarketData object to dictionary format"""
        if not cached_data:
            return None
            
        data = {
            'current_price': cached_data.current_price,
            'day_low': cached_data.day_low,
            'day_high': cached_data.day_high,
            'fifty_two_week_low': cached_data.fifty_two_week_low,
            'fifty_two_week_high': cached_data.fifty_two_week_high,
            'volume': cached_data.volume,
            'avg_volume': cached_data.avg_volume,
            'market_cap': cached_data.market_cap,
            'pe_ratio': cached_data.pe_ratio,
            'forward_pe': cached_data.forward_pe,
            'eps': cached_data.eps,
            'profit_margin': cached_data.profit_margin,
            'dividend_yield': cached_data.dividend_yield,
            'next_earnings_date': cached_data.next_earnings_date,
        }
        
        if cached_data.quarterly_revenue:
            try:
                data['quarterly_revenue'] = json.loads(cached_data.quarterly_revenue)
            except (json.JSONDecodeError, TypeError):
                pass
        if cached_data.quarterly_net_income:
            try:
                data['quarterly_net_income'] = json.loads(cached_data.quarterly_net_income)
            except (json.JSONDecodeError, TypeError):
                pass
                
        return data

    def get_stock_data(self, ticker, position_id=None, force_refresh=False):
        """Get current market data and fundamentals for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            position_id: Optional position ID for caching
            force_refresh: If True, bypass cache and always fetch fresh data
            
        Returns:
            Dictionary with market data, or None if fetch fails and no cached data available
        """
        try:
            # Get cached data for fallback
            cached_data = None
            if position_id:
                cached_data = self.db.get_market_data(position_id)
            
            # Check cache in database if not forcing refresh
            if not force_refresh and cached_data and self._is_cache_valid(cached_data):
                logger.info(f"Using cached data for {ticker}")
                return self._convert_cached_data_to_dict(cached_data)
            
            # Fetch new data from Yahoo Finance with retry logic
            logger.info(f"Fetching fresh data for {ticker} (force_refresh={force_refresh})")
            def fetch_data():
                stock = yf.Ticker(ticker)
                info = stock.info
                return {
                    'current_price': info.get('currentPrice', None),
                    'day_low': info.get('dayLow', None),
                    'day_high': info.get('dayHigh', None),
                    'fifty_two_week_low': info.get('fiftyTwoWeekLow', None),
                    'fifty_two_week_high': info.get('fiftyTwoWeekHigh', None),
                    'volume': info.get('volume', None),
                    'avg_volume': info.get('averageVolume', None),
                    'market_cap': info.get('marketCap', None),
                    'pe_ratio': info.get('trailingPE', None),
                    'forward_pe': info.get('forwardPE', None),
                    'eps': info.get('trailingEps', None),
                    'profit_margin': info.get('profitMargins', None),
                    'dividend_yield': info.get('dividendYield', None),
                    'next_earnings_date': info.get('earningsTimestamp', None),
                }

            data = self._fetch_with_retry(ticker, fetch_data)
            if not data:
                # Fallback to cached data if available
                if cached_data:
                    logger.warning(f"Failed to fetch fresh data for {ticker}, using cached data")
                    return self._convert_cached_data_to_dict(cached_data)
                logger.error(f"Failed to fetch data for {ticker} and no cached data available")
                return None

            # Convert next_earnings_date from timestamp if present
            def convert_timestamp(ts):
                if ts is None:
                    return None
                if isinstance(ts, (int, float)):
                    # Convert Unix timestamp to datetime
                    return datetime.fromtimestamp(ts)
                return ts  # If already a datetime or string, return as is

            data['next_earnings_date'] = convert_timestamp(data.get('next_earnings_date'))

            # Get revenue and net income with retry
            def fetch_financials():
                stock = yf.Ticker(ticker)
                financials = stock.financials
                if not financials.empty:
                    # Convert keys to str for JSON serialization and ensure values are JSON serializable
                    rev = financials.loc['Total Revenue'].head(4).to_dict()
                    net = financials.loc['Net Income'].head(4).to_dict()
                    data['quarterly_revenue'] = {str(k): float(v) if pd.notnull(v) else None for k, v in rev.items()}
                    data['quarterly_net_income'] = {str(k): float(v) if pd.notnull(v) else None for k, v in net.items()}
                return data

            # Try to fetch financials, but don't fail if it doesn't work
            try:
                financials_data = self._fetch_with_retry(ticker, fetch_financials)
                if financials_data:
                    data.update(financials_data)
            except Exception as e:
                logger.warning(f"Failed to fetch financials for {ticker}: {str(e)}")

            # Cache in database if position_id is provided
            if position_id:
                try:
                    self.db.update_market_data(position_id, data)
                except Exception as e:
                    logger.error(f"Failed to update market data in database for {ticker}: {str(e)}")
                    # Still return the data even if caching fails

            return data

        except Exception as e:
            logger.error(f"Error in get_stock_data for {ticker}: {str(e)}")
            # Fallback to cached data if available
            if position_id:
                cached_data = self.db.get_market_data(position_id)
                if cached_data:
                    logger.warning(f"Exception occurred for {ticker}, falling back to cached data")
                    return self._convert_cached_data_to_dict(cached_data)
            return None

    def get_historical_prices(self, ticker, period="1y"):
        """Get historical closing prices with retry logic."""
        def fetch_history():
            stock = yf.Ticker(ticker)
            try:
                hist = stock.history(period=period)
                if not hist.empty:
                    return hist[['Close', 'Open', 'High', 'Low', 'Volume']]
                return None
            except Exception as e:
                logger.error(f"Error fetching historical data for {ticker}: {str(e)}")
                return None

        return self._fetch_with_retry(ticker, fetch_history)

    def get_technical_indicators(self, ticker, position_id=None):
        """Calculate technical indicators for a ticker with retry logic."""
        try:
            # Check cache in database if position_id is provided
            if position_id:
                cached_data = self.db.get_market_data(position_id)
                if cached_data and self._is_cache_valid(cached_data):
                    return {
                        'rsi': cached_data.rsi,
                        'macd': cached_data.macd,
                        'macd_signal': cached_data.macd_signal,
                        'sma_50': cached_data.sma_50,
                        'sma_200': cached_data.sma_200,
                        'is_above_50_sma': cached_data.is_above_50_sma,
                        'is_above_200_sma': cached_data.is_above_200_sma,
                        'rsi_overbought': cached_data.rsi_overbought,
                        'rsi_oversold': cached_data.rsi_oversold,
                        'macd_crossover': cached_data.macd_crossover
                    }

            def fetch_and_calculate():
                # Get historical data in smaller chunks
                hist = pd.DataFrame()
                chunks = ["3mo", "6mo", "9mo", "1y"]
                
                for chunk in chunks:
                    chunk_data = self.get_historical_prices(ticker, chunk)
                    if chunk_data is not None:
                        hist = pd.concat([hist, chunk_data[~chunk_data.index.isin(hist.index)]])
                    time.sleep(2)  # Add delay between chunks
                
                if hist.empty:
                    return None
                
                # Calculate RSI (14-day)
                delta = hist['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                
                # Calculate MACD
                exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
                exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
                macd = exp1 - exp2
                signal = macd.ewm(span=9, adjust=False).mean()
                
                # Calculate 50-day and 200-day SMAs
                sma_50 = hist['Close'].rolling(window=50).mean()
                sma_200 = hist['Close'].rolling(window=200).mean()
                
                return {
                    'rsi': rsi.iloc[-1],
                    'macd': macd.iloc[-1],
                    'macd_signal': signal.iloc[-1],
                    'sma_50': sma_50.iloc[-1],
                    'sma_200': sma_200.iloc[-1],
                    'is_above_50_sma': hist['Close'].iloc[-1] > sma_50.iloc[-1],
                    'is_above_200_sma': hist['Close'].iloc[-1] > sma_200.iloc[-1],
                    'rsi_overbought': rsi.iloc[-1] > 70,
                    'rsi_oversold': rsi.iloc[-1] < 30,
                    'macd_crossover': (macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] <= signal.iloc[-2])
                }

            technical_data = self._fetch_with_retry(ticker, fetch_and_calculate)

            # Cache in database if position_id is provided
            if technical_data and position_id:
                self.db.update_market_data(position_id, {}, technical_data)

            return technical_data

        except Exception as e:
            logger.error(f"Error calculating technical indicators for {ticker}: {str(e)}")
            return None

    def __del__(self):
        """Close database connection when object is destroyed"""
        self.db.close()