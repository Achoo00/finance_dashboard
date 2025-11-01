"""Chart components for the dashboard."""
from typing import Any, Dict, List, Optional, Union, Tuple
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from .base import Component

class BaseChart(Component[None]):
    """Base class for all chart components."""
    
    def __init__(
        self,
        title: Optional[str] = None,
        x_axis_title: Optional[str] = None,
        y_axis_title: Optional[str] = None,
        height: int = 400,
        width: Optional[int] = None,
        template: str = "plotly_white",
        **kwargs
    ):
        """Initialize the base chart.
        
        Args:
            title: Chart title
            x_axis_title: X-axis title
            y_axis_title: Y-axis title
            height: Chart height in pixels
            width: Chart width in pixels (None for auto)
            template: Plotly template name
            **kwargs: Additional styling options
        """
        super().__init__(**kwargs)
        self.title = title
        self.x_axis_title = x_axis_title
        self.y_axis_title = y_axis_title
        self.height = height
        self.width = width
        self.template = template
        self._figure = None
    
    def _get_figure(self) -> go.Figure:
        """Create and return the Plotly figure."""
        return go.Figure()
    
    def _update_layout(self, fig: go.Figure) -> None:
        """Update the figure layout."""
        fig.update_layout(
            title=self.title,
            xaxis_title=self.x_axis_title,
            yaxis_title=self.y_axis_title,
            height=self.height,
            width=self.width,
            template=self.template,
            margin=dict(l=50, r=50, t=50, b=50),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
    
    def render(self, **kwargs) -> None:
        """Render the chart."""
        fig = self._get_figure()
        self._update_layout(fig)
        st.plotly_chart(fig, use_container_width=True, **kwargs)


class LineChart(BaseChart):
    """A line chart component."""
    
    def __init__(
        self,
        data: Union[pd.DataFrame, List[Dict[str, Any]]],
        x: str,
        y: str,
        color: Optional[str] = None,
        line_dash: Optional[str] = None,
        markers: bool = False,
        **kwargs
    ):
        """Initialize a line chart.
        
        Args:
            data: DataFrame or list of dictionaries containing the data
            x: Column name for x-axis
            y: Column name for y-axis
            color: Column name for color grouping
            line_dash: Column name for line dash style
            markers: Whether to show markers on the lines
            **kwargs: Additional arguments for BaseChart
        """
        super().__init__(**kwargs)
        self.data = pd.DataFrame(data) if not isinstance(data, pd.DataFrame) else data
        self.x = x
        self.y = y
        self.color = color
        self.line_dash = line_dash
        self.markers = markers
    
    def _get_figure(self) -> go.Figure:
        """Create and return the Plotly figure."""
        fig = px.line(
            self.data,
            x=self.x,
            y=self.y,
            color=self.color,
            line_dash=self.line_dash,
            markers=self.markers,
            template=self.template
        )
        return fig


class BarChart(BaseChart):
    """A bar chart component."""
    
    def __init__(
        self,
        data: Union[pd.DataFrame, List[Dict[str, Any]]],
        x: str,
        y: str,
        color: Optional[str] = None,
        barmode: str = "relative",  # 'group', 'stack', 'relative', 'overlay'
        horizontal: bool = False,
        **kwargs
    ):
        """Initialize a bar chart.
        
        Args:
            data: DataFrame or list of dictionaries containing the data
            x: Column name for x-axis
            y: Column name for y-axis
            color: Column name for color grouping
            barmode: How bars are displayed ('group', 'stack', 'relative', 'overlay')
            horizontal: Whether to create a horizontal bar chart
            **kwargs: Additional arguments for BaseChart
        """
        super().__init__(**kwargs)
        self.data = pd.DataFrame(data) if not isinstance(data, pd.DataFrame) else data
        self.x = x
        self.y = y
        self.color = color
        self.barmode = barmode
        self.horizontal = horizontal
    
    def _get_figure(self) -> go.Figure:
        """Create and return the Plotly figure."""
        if self.horizontal:
            fig = px.bar(
                self.data,
                y=self.x,
                x=self.y,
                color=self.color,
                barmode=self.barmode,
                orientation='h',
                template=self.template
            )
        else:
            fig = px.bar(
                self.data,
                x=self.x,
                y=self.y,
                color=self.color,
                barmode=self.barmode,
                template=self.template
            )
        return fig


class PieChart(BaseChart):
    """A pie/donut chart component."""
    
    def __init__(
        self,
        data: Union[pd.DataFrame, List[Dict[str, Any]]],
        names: str,
        values: str,
        hole: float = 0.0,
        color: Optional[str] = None,
        **kwargs
    ):
        """Initialize a pie chart.
        
        Args:
            data: DataFrame or list of dictionaries containing the data
            names: Column name for pie slice labels
            values: Column name for pie slice values
            hole: Size of the hole in the middle (0 for pie, >0 for donut)
            color: Column name for color mapping
            **kwargs: Additional arguments for BaseChart
        """
        super().__init__(**kwargs)
        self.data = pd.DataFrame(data) if not isinstance(data, pd.DataFrame) else data
        self.names = names
        self.values = values
        self.hole = hole
        self.color = color
    
    def _get_figure(self) -> go.Figure:
        """Create and return the Plotly figure."""
        fig = px.pie(
            self.data,
            names=self.names,
            values=self.values,
            color=self.color,
            hole=self.hole,
            template=self.template
        )
        return fig


class CandlestickChart(BaseChart):
    """A candlestick chart for financial data."""
    
    def __init__(
        self,
        data: Union[pd.DataFrame, List[Dict[str, Any]]],
        date_column: str = 'date',
        open_column: str = 'open',
        high_column: str = 'high',
        low_column: str = 'low',
        close_column: str = 'close',
        volume_column: Optional[str] = None,
        show_volume: bool = True,
        **kwargs
    ):
        """Initialize a candlestick chart.
        
        Args:
            data: DataFrame or list of dictionaries containing OHLCV data
            date_column: Column name for dates
            open_column: Column name for open prices
            high_column: Column name for high prices
            low_column: Column name for low prices
            close_column: Column name for close prices
            volume_column: Column name for volume data
            show_volume: Whether to show volume bars at the bottom
            **kwargs: Additional arguments for BaseChart
        """
        super().__init__(**kwargs)
        self.data = pd.DataFrame(data) if not isinstance(data, pd.DataFrame) else data
        self.date_column = date_column
        self.open_column = open_column
        self.high_column = high_column
        self.low_column = low_column
        self.close_column = close_column
        self.volume_column = volume_column
        self.show_volume = show_volume and (volume_column is not None)
        
        if self.show_volume:
            self.height = (self.height or 600) + 100  # Add space for volume subplot
    
    def _get_figure(self) -> go.Figure:
        """Create and return the Plotly figure."""
        if self.show_volume:
            # Create figure with secondary y-axis for volume
            fig = make_subplots(
                rows=2, 
                cols=1, 
                shared_xaxes=True, 
                vertical_spacing=0.03,
                row_heights=[0.7, 0.3],
                subplot_titles=('Price', 'Volume')
            )
            
            # Add candlestick
            fig.add_trace(
                go.Candlestick(
                    x=self.data[self.date_column],
                    open=self.data[self.open_column],
                    high=self.data[self.high_column],
                    low=self.data[self.low_column],
                    close=self.data[self.close_column],
                    name="OHLC"
                ),
                row=1, col=1
            )
            
            # Add volume bars
            fig.add_trace(
                go.Bar(
                    x=self.data[self.date_column],
                    y=self.data[self.volume_column],
                    showlegend=False,
                    marker_color='rgba(100, 100, 100, 0.7)'
                ),
                row=2, col=1
            )
            
            # Update layout for volume subplot
            fig.update_yaxes(title_text="Price", row=1, col=1)
            fig.update_yaxes(title_text="Volume", row=2, col=1)
            
        else:
            # Simple candlestick without volume
            fig = go.Figure(
                data=[go.Candlestick(
                    x=self.data[self.date_column],
                    open=self.data[self.open_column],
                    high=self.data[self.high_column],
                    low=self.data[self.low_column],
                    close=self.data[self.close_column],
                    name="OHLC"
                )]
            )
        
        # Update x-axis settings
        fig.update_xaxes(
            rangeslider_visible=False,
            rangebreaks=[
                # NOTE: Remove dates with no trading
                dict(bounds=["sat", "mon"]),  # hide weekends
                dict(bounds=[20, 15], pattern="hour"),  # hide hours outside of 9:30am-4pm
            ]
        )
        
        return fig
