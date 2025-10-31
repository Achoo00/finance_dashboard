import yaml
from datetime import datetime
import yfinance as yf
from data_collector import StockDataCollector
import pandas as pd
from database import DatabaseManager
import logging
from contextlib import contextmanager

logging.basicConfig(level=logging.DEBUG)  # Changed to DEBUG level for more detailed logging
logger = logging.getLogger(__name__)

class StockDataYAMLExporter:
    # AI Analysis Prompts
    ANALYSIS_PROMPTS = {
        'technical': """Based on this YAML stock data, suggest if I should enter, hold, or exit this position. Consider the RSI, MACD, 52-week range, and PE ratios. If the stock is technically overbought or undervalued, explain your rationale.""",
        
        'valuation': """Here's the valuation and technical data for {ticker}. Compare it to the sector average or competitors and tell me if it's currently overvalued or a good entry point.""",
        
        'news': """Here's the YAML data for {ticker}. Look up recent news headlines about this stock and explain how any events (e.g., product launches, legal actions, or executive changes) could impact its near-term price or long-term outlook.""",
        
        'sentiment': """Use the YAML sentiment snapshot and supplement with Reddit, Twitter, and financial news sentiment. Is the market currently optimistic or skeptical about this stock? Should that influence my position?""",
        
        'macro': """Based on this YAML and current market events (e.g., interest rate decisions, inflation reports), explain how macro trends might affect this stock and whether to adjust my exposure."""
    }

    def __init__(self):
        self.collector = StockDataCollector()

    @contextmanager
    def _get_db_connection(self):
        """Context manager for database connections"""
        db = None
        try:
            db = DatabaseManager()
            yield db
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            raise
        finally:
            if db:
                db.close()
                logger.debug("Database connection closed")

    def _format_percentage(self, value):
        """Format decimal to percentage string"""
        if value is None:
            return None
        return f"{value * 100:.1f}%"

    def _get_recent_news(self, ticker):
        """Get recent news headlines for a ticker"""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news[:5]  # Get last 5 news items
            return [item['title'] for item in news] if news else []
        except Exception as e:
            logger.warning(f"Could not fetch news for {ticker}: {str(e)}")
            return []

    def _get_position_data(self, db, position):
        """Get position data and handle any errors"""
        try:
            logger.debug(f"Getting position data for ID={position.id}, Ticker={position.ticker}")
            return {
                'entry_date': position.entry_date.strftime('%Y-%m-%d'),
                'entry_price': position.entry_price,
                'quantity': position.quantity,
                'cost_basis': position.entry_price * position.quantity,
                'notes': position.notes if position.notes else None
            }
        except Exception as e:
            logger.error(f"Error processing position data: {str(e)}")
            return None

    def _get_market_data(self, db, position_id, position_data):
        """Get market data and handle any errors"""
        try:
            logger.debug(f"Getting market data for position_id={position_id} (type={type(position_id)})")
            cached_data = db.get_market_data(position_id)
            if not cached_data:
                logger.warning(f"No market data found for position_id {position_id}")
                return None, None, None

            # Track which data categories are available
            data_availability = {
                'basic_price': False,
                'market_stats': False,
                'fundamentals': False,
                'technicals': False,
                'financials': False
            }

            market_data = {}

            # Basic price data
            if cached_data.current_price:
                market_data['current_price'] = cached_data.current_price
                data_availability['basic_price'] = True

            # Market statistics
            if all(getattr(cached_data, attr) is not None for attr in ['day_low', 'day_high', 'volume', 'avg_volume']):
                market_data.update({
                    'day_low': cached_data.day_low,
                    'day_high': cached_data.day_high,
                    'fifty_two_week_low': cached_data.fifty_two_week_low,
                    'fifty_two_week_high': cached_data.fifty_two_week_high,
                    'volume': cached_data.volume,
                    'avg_volume': cached_data.avg_volume,
                    'market_cap': cached_data.market_cap
                })
                data_availability['market_stats'] = True

            # Fundamental data
            if all(getattr(cached_data, attr) is not None for attr in ['pe_ratio', 'eps', 'profit_margin']):
                market_data.update({
                    'pe_ratio': cached_data.pe_ratio,
                    'forward_pe': cached_data.forward_pe,
                    'eps': cached_data.eps,
                    'profit_margin': cached_data.profit_margin,
                    'dividend_yield': cached_data.dividend_yield
                })
                data_availability['fundamentals'] = True

            # Technical indicators
            if cached_data.rsi is not None:
                market_data['technical_indicators'] = {
                    'rsi': round(cached_data.rsi, 2),
                    'macd': {
                        'value': round(cached_data.macd, 2) if cached_data.macd else None,
                        'signal': round(cached_data.macd_signal, 2) if cached_data.macd_signal else None,
                        'crossover': cached_data.macd_crossover
                    },
                    'moving_averages': {
                        'sma_50': round(cached_data.sma_50, 2) if cached_data.sma_50 else None,
                        'sma_200': round(cached_data.sma_200, 2) if cached_data.sma_200 else None,
                        'above_50_sma': cached_data.is_above_50_sma,
                        'above_200_sma': cached_data.is_above_200_sma
                    }
                }
                data_availability['technicals'] = True

            # Quarterly financials
            if cached_data.quarterly_revenue:
                try:
                    market_data['quarterly_financials'] = {
                        'revenue': yaml.safe_load(cached_data.quarterly_revenue),
                        'net_income': yaml.safe_load(cached_data.quarterly_net_income) if cached_data.quarterly_net_income else None
                    }
                    data_availability['financials'] = True
                except yaml.YAMLError as e:
                    logger.error(f"Error parsing quarterly financials: {str(e)}")

            # Add performance metrics if we have current price
            if cached_data.current_price and position_data:
                current_value = cached_data.current_price * position_data['quantity']
                gain_loss = current_value - position_data['cost_basis']
                position_data.update({
                    'current_value': current_value,
                    'gain_loss': gain_loss,
                    'gain_loss_percentage': f"{(gain_loss / position_data['cost_basis'] * 100):.2f}%"
                })

            return market_data, cached_data, data_availability
        except Exception as e:
            logger.error(f"Error processing market data: {str(e)}")
            return None, None, None

    def generate_stock_yaml(self, ticker, position_id=None):
        """Generate YAML format analysis for a stock"""
        logger.info(f"Starting YAML generation for ticker={ticker}, position_id={position_id} (type={type(position_id)})")
        
        # Initialize basic data structure
        data = {
            'ticker': ticker,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'data_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_availability': {
                'status': 'partial',
                'available_data': ['basic_info']
            }
        }

        try:
            with self._get_db_connection() as db:
                # Get position data if position_id is provided
                if position_id:
                    # Convert position_id to integer if it's not already
                    position_id = int(position_id)
                    logger.debug(f"Fetching position from database for position_id={position_id} (type={type(position_id)})")
                    position = db.get_position(position_id)
                    logger.info(f"Found position: {position is not None}")
                    if position:
                        logger.debug(f"Position details - ID: {position.id}, Ticker: {position.ticker}, Entry Price: {position.entry_price}")
                        
                        # Verify ticker matches position
                        if position.ticker != ticker:
                            logger.warning(f"Ticker mismatch! Requested ticker={ticker}, but position has ticker={position.ticker}")
                            return yaml.dump(data, sort_keys=False, allow_unicode=True)
                        
                        position_data = self._get_position_data(db, position)
                        if position_data:
                            data['position'] = position_data
                            data['data_availability']['available_data'].append('position')

                        # Get market data
                        logger.debug(f"Fetching market data for position_id={position_id}")
                        market_data, cached_data, data_availability = self._get_market_data(db, position_id, position_data)
                        
                        if market_data and cached_data:
                            logger.debug(f"Market data found - Last Updated: {cached_data.last_updated}, Current Price: {cached_data.current_price}")
                            # Update data availability and timestamp
                            data['data_timestamp'] = cached_data.last_updated.strftime('%Y-%m-%d %H:%M:%S')
                            
                            # Update available data categories
                            for category, available in data_availability.items():
                                if available:
                                    data['data_availability']['available_data'].append(category)

                            # Set overall status
                            all_data_available = all(data_availability.values())
                            data['data_availability']['status'] = 'full' if all_data_available else 'partial'
                            
                            # Add market data to YAML based on availability
                            if data_availability['basic_price']:
                                data['current_price'] = market_data['current_price']

                            if data_availability['market_stats']:
                                data.update({
                                    '52_week_range': [
                                        market_data['fifty_two_week_low'],
                                        market_data['fifty_two_week_high']
                                    ],
                                    'volume': {
                                        'current': market_data['volume'],
                                        'average': market_data['avg_volume']
                                    },
                                    'market_cap': market_data['market_cap']
                                })

                            if data_availability['fundamentals']:
                                data['valuation'] = {
                                    'pe_ratio': {
                                        'trailing': market_data['pe_ratio'],
                                        'forward': market_data['forward_pe']
                                    },
                                    'eps': market_data['eps'],
                                    'profit_margin': self._format_percentage(market_data['profit_margin']),
                                    'dividend_yield': self._format_percentage(market_data['dividend_yield'])
                                }

                            if data_availability['technicals']:
                                data['technical_indicators'] = market_data['technical_indicators']
                                data['flags'] = {
                                    'rsi_overbought': cached_data.rsi_overbought,
                                    'rsi_oversold': cached_data.rsi_oversold,
                                    'bullish_macd_cross': cached_data.macd_crossover,
                                    'above_200_sma': cached_data.is_above_200_sma,
                                    'at_52_week_high': (
                                        cached_data.current_price and 
                                        cached_data.fifty_two_week_high and
                                        cached_data.current_price >= cached_data.fifty_two_week_high * 0.95
                                    )
                                }

                            if data_availability['financials']:
                                data['quarterly_financials'] = market_data['quarterly_financials']

                # Add recent news
                news = self._get_recent_news(ticker)
                if news:
                    data['recent_news'] = news
                    data['data_availability']['available_data'].append('news')

            # Add AI analysis prompts
            data['ai_analysis_prompts'] = {
                name: prompt.format(ticker=ticker) for name, prompt in self.ANALYSIS_PROMPTS.items()
            }

            logger.info(f"Final data availability: {data['data_availability']}")
            return yaml.dump(data, sort_keys=False, allow_unicode=True)

        except Exception as e:
            logger.error(f"Error generating YAML for {ticker}: {str(e)}")
            return yaml.dump(data, sort_keys=False, allow_unicode=True)  # Return partial data with error status

    def export_portfolio_yaml(self, portfolio_df):
        """Generate YAML analysis for entire portfolio"""
        try:
            portfolio_data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'portfolio_summary': {
                    'total_positions': len(portfolio_df),
                    'total_value': portfolio_df['Market Value'].sum() if 'Market Value' in portfolio_df.columns else None,
                    'total_gain_loss': portfolio_df['Gain/Loss'].sum() if 'Gain/Loss' in portfolio_df.columns else None
                },
                'positions': {}
            }

            for _, position in portfolio_df.iterrows():
                ticker = position['ticker']
                # Convert position ID to integer
                position_id = int(position['id'])
                stock_yaml = self.generate_stock_yaml(ticker, position_id)
                if stock_yaml:
                    try:
                        portfolio_data['positions'][ticker] = yaml.safe_load(stock_yaml)
                    except yaml.YAMLError as e:
                        logger.error(f"Error parsing YAML for {ticker}: {str(e)}")
                        continue

            # Add portfolio-level AI analysis prompts
            portfolio_data['ai_analysis_prompts'] = {
                'portfolio_technical': """Based on this portfolio YAML data, analyze the technical health of each position. Which stocks show concerning technical signals? Which ones have strong momentum?""",
                'portfolio_diversification': """Review this portfolio's composition and suggest any rebalancing needed. Are there overweight positions or sectors that need attention?""",
                'portfolio_risk': """Considering the technical indicators, valuations, and current market conditions, what are the biggest risks in this portfolio? How can they be mitigated?"""
            }

            return yaml.dump(portfolio_data, sort_keys=False, allow_unicode=True)

        except Exception as e:
            logger.error(f"Error generating portfolio YAML: {str(e)}")
            return None 