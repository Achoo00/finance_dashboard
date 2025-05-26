import yaml
from datetime import datetime
import yfinance as yf
from data_collector import StockDataCollector
import pandas as pd

class StockDataYAMLExporter:
    def __init__(self):
        self.collector = StockDataCollector()

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
        except:
            return []

    def generate_stock_yaml(self, ticker, portfolio_id=None):
        """Generate YAML format analysis for a stock"""
        # Get market data
        market_data = self.collector.get_stock_data(ticker, portfolio_id)
        technical_data = self.collector.get_technical_indicators(ticker, portfolio_id)
        
        if not market_data:
            return None

        # Build YAML structure
        data = {
            'ticker': ticker,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'current_price': market_data.get('current_price'),
            '52_week_range': [
                market_data.get('fifty_two_week_low'),
                market_data.get('fifty_two_week_high')
            ],
            'volume': {
                'current': market_data.get('volume'),
                'average': market_data.get('avg_volume')
            },
            'market_cap': market_data.get('market_cap'),
            'valuation': {
                'pe_ratio': {
                    'trailing': market_data.get('pe_ratio'),
                    'forward': market_data.get('forward_pe')
                },
                'eps': market_data.get('eps'),
                'profit_margin': self._format_percentage(market_data.get('profit_margin')),
                'dividend_yield': self._format_percentage(market_data.get('dividend_yield'))
            }
        }

        # Add technical indicators if available
        if technical_data:
            data['technical_indicators'] = {
                'rsi': round(technical_data.get('rsi', 0), 2),
                'macd': {
                    'value': round(technical_data.get('macd', 0), 2),
                    'signal': round(technical_data.get('macd_signal', 0), 2),
                    'crossover': technical_data.get('macd_crossover', False)
                },
                'moving_averages': {
                    'sma_50': round(technical_data.get('sma_50', 0), 2),
                    'sma_200': round(technical_data.get('sma_200', 0), 2),
                    'above_50_sma': technical_data.get('is_above_50_sma', False),
                    'above_200_sma': technical_data.get('is_above_200_sma', False)
                }
            }

            # Add technical flags
            data['flags'] = {
                'rsi_overbought': technical_data.get('rsi_overbought', False),
                'rsi_oversold': technical_data.get('rsi_oversold', False),
                'bullish_macd_cross': technical_data.get('macd_crossover', False),
                'above_200_sma': technical_data.get('is_above_200_sma', False),
                'at_52_week_high': (
                    market_data.get('current_price') and 
                    market_data.get('fifty_two_week_high') and
                    market_data.get('current_price') >= market_data.get('fifty_two_week_high') * 0.95
                )
            }

        # Add recent news
        news = self._get_recent_news(ticker)
        if news:
            data['recent_news'] = news

        return yaml.dump(data, sort_keys=False, allow_unicode=True)

    def export_portfolio_yaml(self, portfolio_df):
        """Generate YAML analysis for entire portfolio"""
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
            stock_yaml = self.generate_stock_yaml(ticker, position['id'])
            if stock_yaml:
                portfolio_data['positions'][ticker] = yaml.safe_load(stock_yaml)

        return yaml.dump(portfolio_data, sort_keys=False, allow_unicode=True) 