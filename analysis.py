import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

class PortfolioAnalyzer:
    @staticmethod
    def create_portfolio_composition_chart(portfolio_df):
        """Create a pie chart showing portfolio composition by value."""
        if portfolio_df.empty or 'Market Value' not in portfolio_df.columns:
            return None
        
        # Use 'Ticker' (capitalized) since that's what the DataFrame has after renaming
        ticker_col = 'Ticker' if 'Ticker' in portfolio_df.columns else 'ticker'
        
        fig = px.pie(
            portfolio_df,
            values='Market Value',
            names=ticker_col,
            title='Portfolio Composition',
            hole=0.3
        )
        fig.update_layout(showlegend=True)
        return fig

    @staticmethod
    def create_portfolio_performance_chart(portfolio_df):
        """Create a bar chart showing gains/losses by position."""
        # Check for available columns (may be 'Return %' or 'Gain/Loss' or 'gain_loss_pct')
        if portfolio_df.empty:
            return None
        
        # Determine which columns are available
        ticker_col = 'Ticker' if 'Ticker' in portfolio_df.columns else 'ticker'
        value_col = None
        for col in ['Return %', 'Gain/Loss', 'gain_loss_pct']:
            if col in portfolio_df.columns:
                value_col = col
                break
        
        if not value_col:
            return None
        
        colors = ['red' if x < 0 else 'green' for x in portfolio_df[value_col]]
        
        # Format text based on whether it's a percentage or dollar amount
        if value_col == 'Return %' or value_col == 'gain_loss_pct':
            text_values = portfolio_df[value_col].apply(lambda x: f'{x:.2f}%')
            y_axis_title = 'Return %'
        else:
            text_values = portfolio_df[value_col].apply(lambda x: f'${x:,.2f}')
            y_axis_title = 'Gain/Loss ($)'
        
        fig = go.Figure(data=[
            go.Bar(
                x=portfolio_df[ticker_col],
                y=portfolio_df[value_col],
                marker_color=colors,
                text=text_values,
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title='Portfolio Performance by Position',
            xaxis_title='Ticker',
            yaxis_title=y_axis_title,
            showlegend=False
        )
        return fig

    @staticmethod
    def create_technical_chart(hist_data, ticker, show_options=None, time_range=None):
        """Create a technical analysis chart with selectable indicators.
        
        Args:
            hist_data: Historical price data DataFrame
            ticker: Stock ticker symbol
            show_options: Dict of boolean flags for each indicator
                {
                    'candlesticks': bool,
                    'bollinger': bool,
                    'sma': bool,
                    'rsi': bool,
                    'volume': bool
                }
            time_range: String indicating the time range to display
                Options: '1D', '5D', '1M', '6M', 'YTD', '1Y', '5Y', 'ALL'
        """
        if hist_data.empty:
            return None
            
        # Filter data based on time range
        if time_range and time_range != 'ALL':
            end_date = hist_data.index.max()
            if time_range == '1D':
                start_date = end_date - pd.Timedelta(days=1)
            elif time_range == '5D':
                start_date = end_date - pd.Timedelta(days=5)
            elif time_range == '1M':
                start_date = end_date - pd.Timedelta(days=30)
            elif time_range == '6M':
                start_date = end_date - pd.Timedelta(days=180)
            elif time_range == 'YTD':
                start_date = pd.Timestamp(end_date.year, 1, 1)
            elif time_range == '1Y':
                start_date = end_date - pd.Timedelta(days=365)
            elif time_range == '5Y':
                start_date = end_date - pd.Timedelta(days=365*5)
            
            hist_data = hist_data[hist_data.index >= start_date]
            
        # Default to showing everything if no options provided
        if show_options is None:
            show_options = {
                'candlesticks': True,
                'bollinger': True,
                'sma': True,
                'rsi': True,
                'volume': True
            }
        
        # Calculate indicators (only if needed)
        if show_options.get('bollinger'):
            bb = BollingerBands(close=hist_data['Close'])
            hist_data['BB_high'] = bb.bollinger_hband()
            hist_data['BB_low'] = bb.bollinger_lband()
            hist_data['BB_mid'] = bb.bollinger_mavg()
        
        if show_options.get('sma'):
            hist_data['SMA_50'] = SMAIndicator(close=hist_data['Close'], window=50).sma_indicator()
            hist_data['SMA_200'] = SMAIndicator(close=hist_data['Close'], window=200).sma_indicator()
        
        if show_options.get('rsi'):
            hist_data['RSI'] = RSIIndicator(close=hist_data['Close']).rsi()
        
        # Create subplots based on what's shown
        row_heights = [0.7]  # Main price chart
        if show_options.get('volume'):
            row_heights.append(0.15)  # Volume
        if show_options.get('rsi'):
            row_heights.append(0.15)  # RSI
        
        fig = go.Figure()
        
        # Track min and max values for y-axis scaling
        price_values = []
        
        # Main price chart
        if show_options.get('candlesticks'):
            fig.add_trace(go.Candlestick(
                x=hist_data.index,
                open=hist_data['Open'],
                high=hist_data['High'],
                low=hist_data['Low'],
                close=hist_data['Close'],
                name='Price'
            ))
            price_values.extend([
                hist_data['High'].max(),
                hist_data['Low'].min()
            ])
        else:
            # Line chart alternative
            fig.add_trace(go.Scatter(
                x=hist_data.index,
                y=hist_data['Close'],
                name='Price',
                line=dict(color='black')
            ))
            price_values.extend([
                hist_data['Close'].max(),
                hist_data['Close'].min()
            ])
        
        # Add Bollinger Bands if selected
        if show_options.get('bollinger'):
            fig.add_trace(go.Scatter(
                x=hist_data.index,
                y=hist_data['BB_high'],
                line=dict(color='gray', dash='dash'),
                name='BB Upper'
            ))
            
            fig.add_trace(go.Scatter(
                x=hist_data.index,
                y=hist_data['BB_low'],
                line=dict(color='gray', dash='dash'),
                name='BB Lower',
                fill='tonexty'
            ))
            price_values.extend([
                hist_data['BB_high'].max(),
                hist_data['BB_low'].min()
            ])
        
        # Add SMAs if selected
        if show_options.get('sma'):
            fig.add_trace(go.Scatter(
                x=hist_data.index,
                y=hist_data['SMA_50'],
                line=dict(color='blue'),
                name='SMA 50'
            ))
            
            fig.add_trace(go.Scatter(
                x=hist_data.index,
                y=hist_data['SMA_200'],
                line=dict(color='red'),
                name='SMA 200'
            ))
            price_values.extend([
                hist_data['SMA_50'].max(),
                hist_data['SMA_50'].min(),
                hist_data['SMA_200'].max(),
                hist_data['SMA_200'].min()
            ])
        
        # Calculate y-axis range with padding
        if price_values:
            y_min = min(v for v in price_values if pd.notna(v))
            y_max = max(v for v in price_values if pd.notna(v))
            y_padding = (y_max - y_min) * 0.05  # 5% padding
            y_range = [y_min - y_padding, y_max + y_padding]
        else:
            y_range = None
        
        # Add RSI if selected
        if show_options.get('rsi'):
            fig.add_trace(go.Scatter(
                x=hist_data.index,
                y=hist_data['RSI'],
                name='RSI',
                yaxis="y2"
            ))
            
            # Add RSI overbought/oversold lines
            fig.add_hline(y=70, line_dash="dash", line_color="red", line_width=1, opacity=0.5)
            fig.add_hline(y=30, line_dash="dash", line_color="green", line_width=1, opacity=0.5)
            
            # Add a new y-axis for RSI
            fig.update_layout(
                yaxis2=dict(
                    title="RSI",
                    overlaying="y",
                    side="right",
                    range=[0, 100]
                )
            )
        
        # Add volume if selected
        if show_options.get('volume'):
            colors = ['red' if row['Open'] > row['Close'] else 'green' for _, row in hist_data.iterrows()]
            fig.add_trace(go.Bar(
                x=hist_data.index,
                y=hist_data['Volume'],
                name='Volume',
                marker_color=colors,
                yaxis="y3"
            ))
            
            # Add a new y-axis for volume
            fig.update_layout(
                yaxis3=dict(
                    title="Volume",
                    overlaying="y",
                    side="right",
                    anchor="free",
                    position=1
                )
            )
        
        # Update layout with dynamic y-axis range
        fig.update_layout(
            title=f'{ticker} Technical Analysis ({time_range if time_range else "ALL"})',
            yaxis_title='Price',
            xaxis_title='Date',
            template='plotly_white',
            height=800,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            yaxis=dict(
                range=y_range
            ) if y_range else dict()
        )
        
        return fig

    @staticmethod
    def create_correlation_matrix(portfolio_df, price_history):
        """Create a correlation matrix heatmap of portfolio assets."""
        if not price_history or len(price_history) < 2:
            return None
            
        # Create a DataFrame with daily returns
        returns_df = pd.DataFrame()
        for ticker in portfolio_df['ticker']:
            if ticker in price_history:
                returns_df[ticker] = price_history[ticker]['Close'].pct_change()
        
        if returns_df.empty:
            return None
            
        # Calculate correlation matrix
        corr_matrix = returns_df.corr()
        
        # Create heatmap
        fig = px.imshow(
            corr_matrix,
            title='Portfolio Correlation Matrix',
            color_continuous_scale='RdBu',
            aspect='auto'
        )
        
        # Update layout
        fig.update_layout(
            width=800,
            height=800
        )
        
        return fig

    @staticmethod
    def calculate_portfolio_metrics(portfolio_df):
        """Calculate key portfolio metrics."""
        if portfolio_df.empty:
            return {}
            
        total_value = portfolio_df['Market Value'].sum()
        total_cost = (portfolio_df['entry_price'] * portfolio_df['quantity']).sum()
        total_gain_loss = portfolio_df['Gain/Loss'].sum()
        
        metrics = {
            'Total Value': total_value,
            'Total Cost': total_cost,
            'Total Gain/Loss': total_gain_loss,
            'Return (%)': (total_gain_loss / total_cost * 100) if total_cost > 0 else 0,
            'Number of Positions': len(portfolio_df),
            'Average Position Size': total_value / len(portfolio_df) if len(portfolio_df) > 0 else 0
        }
        
        return metrics 