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
        
        fig = px.pie(
            portfolio_df,
            values='Market Value',
            names='ticker',
            title='Portfolio Composition',
            hole=0.3
        )
        fig.update_layout(showlegend=True)
        return fig

    @staticmethod
    def create_portfolio_performance_chart(portfolio_df):
        """Create a bar chart showing gains/losses by position."""
        if portfolio_df.empty or 'Gain/Loss' not in portfolio_df.columns:
            return None
        
        colors = ['red' if x < 0 else 'green' for x in portfolio_df['Gain/Loss']]
        
        fig = go.Figure(data=[
            go.Bar(
                x=portfolio_df['ticker'],
                y=portfolio_df['Gain/Loss'],
                marker_color=colors,
                text=portfolio_df['Gain/Loss'].apply(lambda x: f'${x:,.2f}'),
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title='Portfolio Performance by Position',
            xaxis_title='Ticker',
            yaxis_title='Gain/Loss ($)',
            showlegend=False
        )
        return fig

    @staticmethod
    def create_technical_chart(hist_data, ticker):
        """Create a technical analysis chart with price, volume, and indicators."""
        if hist_data.empty:
            return None
        
        # Calculate indicators
        bb = BollingerBands(close=hist_data['Close'])
        hist_data['BB_high'] = bb.bollinger_hband()
        hist_data['BB_low'] = bb.bollinger_lband()
        hist_data['BB_mid'] = bb.bollinger_mavg()
        
        hist_data['SMA_50'] = SMAIndicator(close=hist_data['Close'], window=50).sma_indicator()
        hist_data['SMA_200'] = SMAIndicator(close=hist_data['Close'], window=200).sma_indicator()
        hist_data['RSI'] = RSIIndicator(close=hist_data['Close']).rsi()
        
        # Create the main price chart
        fig = go.Figure()
        
        # Candlestick chart
        fig.add_trace(go.Candlestick(
            x=hist_data.index,
            open=hist_data['Open'],
            high=hist_data['High'],
            low=hist_data['Low'],
            close=hist_data['Close'],
            name='Price'
        ))
        
        # Add Bollinger Bands
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
        
        # Add SMAs
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
        
        # Update layout
        fig.update_layout(
            title=f'{ticker} Technical Analysis',
            yaxis_title='Price',
            xaxis_title='Date',
            template='plotly_white',
            height=800
        )
        
        # Add RSI subplot
        fig.add_trace(go.Scatter(
            x=hist_data.index,
            y=hist_data['RSI'],
            name='RSI',
            yaxis="y2"
        ))
        
        # Add a new y-axis for RSI
        fig.update_layout(
            yaxis2=dict(
                title="RSI",
                overlaying="y",
                side="right",
                range=[0, 100]
            )
        )
        
        # Add RSI overbought/oversold lines
        fig.add_hline(y=70, line_dash="dash", line_color="red", line_width=1, opacity=0.5)
        fig.add_hline(y=30, line_dash="dash", line_color="green", line_width=1, opacity=0.5)
        
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