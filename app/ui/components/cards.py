"""Card components for the dashboard."""
from typing import Optional, Union, List, Dict, Any
import streamlit as st
from .base import Component


class Card(Component[None]):
    """A flexible card component with a header and content."""
    
    def __init__(
        self,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        content: Optional[Union[str, Component, List[Component]]] = None,
        **kwargs
    ):
        """Initialize a card component.
        
        Args:
            title: Card title
            subtitle: Optional subtitle
            content: Main content (string or component)
            **kwargs: Additional styling options
        """
        super().__init__(**kwargs)
        self.title = title
        self.subtitle = subtitle
        self.content = content or []
        if not isinstance(self.content, list):
            self.content = [self.content]
    
    def add_content(self, content: Union[str, Component]) -> 'Card':
        """Add content to the card."""
        self.content.append(content)
        return self
    
    def render(self, **kwargs) -> None:
        """Render the card with its content."""
        with st.container():
            # Card header
            if self.title or self.subtitle:
                with st.container():
                    if self.title:
                        st.subheader(self.title)
                    if self.subtitle:
                        st.caption(self.subtitle)
                st.divider()
            
            # Card content
            for item in self.content:
                if isinstance(item, str):
                    st.markdown(item)
                elif hasattr(item, 'render'):
                    item.render(**kwargs)
                else:
                    st.write(item)


class StatCard(Component[None]):
    """A card component for displaying statistics with optional trend indicators."""
    
    def __init__(
        self,
        title: str,
        value: Union[str, int, float],
        change: Optional[float] = None,
        icon: Optional[str] = None,
        **kwargs
    ):
        """Initialize a stat card.
        
        Args:
            title: Statistic name/label
            value: The main value to display
            change: Percentage change (positive or negative)
            icon: Optional icon (emoji or icon name)
            **kwargs: Additional styling options
        """
        super().__init__(**kwargs)
        self.title = title
        self.value = value
        self.change = change
        self.icon = icon
    
    def _get_change_style(self) -> Dict[str, str]:
        """Get styling for the change indicator."""
        if self.change is None:
            return {}
        
        if self.change >= 0:
            return {
                'color': 'green',
                'icon': '▲',
                'prefix': '+'
            }
        else:
            return {
                'color': 'red',
                'icon': '▼',
                'prefix': ''
            }
    
    def render(self, **kwargs) -> None:
        """Render the stat card."""
        with st.container():
            # Card container with some padding
            with st.container():
                # Header with title and icon
                header_cols = st.columns([1, 20])
                with header_cols[0]:
                    if self.icon:
                        st.markdown(f"### {self.icon}")
                
                with header_cols[1]:
                    st.markdown(f"**{self.title}**")
                
                # Main value
                st.markdown(f"## {self.value}")
                
                # Change indicator
                if self.change is not None:
                    style = self._get_change_style()
                    st.markdown(
                        f"<span style='color: {style['color']}'>"
                        f"{style['icon']} {style['prefix']}{abs(self.change)}%"
                        "</span>",
                        unsafe_allow_html=True
                    )


class PortfolioCard(Component[None]):
    """A specialized card for displaying portfolio information."""
    
    def __init__(
        self,
        portfolio_name: str,
        total_value: float,
        currency: str = "USD",
        change_24h: Optional[float] = None,
        holdings: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        """Initialize a portfolio card.
        
        Args:
            portfolio_name: Name of the portfolio
            total_value: Total portfolio value
            currency: Currency symbol
            change_24h: 24-hour change percentage
            holdings: List of holdings with 'symbol' and 'allocation' keys
            **kwargs: Additional styling options
        """
        super().__init__(**kwargs)
        self.portfolio_name = portfolio_name
        self.total_value = total_value
        self.currency = currency
        self.change_24h = change_24h
        self.holdings = holdings or []
    
    def _format_currency(self, value: float) -> str:
        """Format currency value."""
        return f"{self.currency} {value:,.2f}"
    
    def render(self, **kwargs) -> None:
        """Render the portfolio card."""
        with Card(title=self.portfolio_name, **kwargs) as card:
            # Total value and change
            cols = st.columns([2, 1])
            with cols[0]:
                st.markdown(f"### {self._format_currency(self.total_value)}")
            with cols[1]:
                if self.change_24h is not None:
                    style = StatCard._get_change_style(self)
                    st.markdown(
                        f"<div style='text-align: right; color: {style['color']}'>"
                        f"{style['icon']} {style['prefix']}{abs(self.change_24h)}% (24h)"
                        "</div>",
                        unsafe_allow_html=True
                    )
            
            # Holdings breakdown
            if self.holdings:
                st.subheader("Holdings", divider=True)
                for holding in self.holdings:
                    cols = st.columns([3, 2, 1])
                    with cols[0]:
                        st.markdown(f"**{holding['symbol']}**")
                    with cols[1]:
                        st.progress(holding['allocation'] / 100)
                    with cols[2]:
                        st.markdown(f"{holding['allocation']:.1f}%")


# Add context manager support to Card
Card.__enter__ = lambda self: self
Card.__exit__ = lambda self, exc_type, exc_val, exc_tb: self.render()
