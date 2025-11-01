"""
Grid layout component for creating responsive grid layouts.

This module provides a Grid component that allows you to create responsive
grid layouts with a specified number of columns. Each cell in the grid
can contain any Streamlit component or content.
"""
from typing import Any, Dict, List, Optional, Union
import streamlit as st
from .base import LayoutComponent

class Grid(LayoutComponent[None]):
    """A responsive grid layout component.
    
    Example:
        ```python
        grid = Grid(columns=2, gap="1rem")
        with grid.container():
            with grid.column():
                st.metric("Total Value", "$10,000")
            with grid.column():
                st.metric("Daily Change", "+$250")
        ```
    """
    
    def __init__(
        self, 
        columns: int = 2, 
        gap: str = "1rem",
        vertical_align: str = "start",
        **kwargs
    ):
        """Initialize the grid layout.
        
        Args:
            columns: Number of columns in the grid (1-12)
            gap: Gap between grid items (CSS value, e.g., "1rem", "10px 5px")
            vertical_align: Vertical alignment of grid items (start, center, end, stretch)
            **kwargs: Additional arguments to pass to the grid container
        """
        super().__init__(**kwargs)
        self.columns = max(1, min(12, columns))  # Limit to 1-12 columns
        self.gap = gap
        self.vertical_align = vertical_align
        self._container = None
        self._current_column = 0
    
    def container(self, **container_kwargs):
        """Create a container for the grid.
        
        Args:
            **container_kwargs: Additional arguments to pass to the container
        """
        self._container = st.container(**container_kwargs)
        self._current_column = 0
        return self._container
    
    def column(self, width: int = 1, **column_kwargs):
        """Create a column in the grid.
        
        Args:
            width: Width of the column in grid units (1-12)
            **column_kwargs: Additional arguments to pass to the column container
        """
        if self._container is None:
            self.container()
            
        width = max(1, min(12, width))  # Limit to 1-12
        
        # Calculate the number of columns to skip
        if self._current_column + width > self.columns:
            # Move to the next row
            st.write("<div style='flex-basis: 100%; height: 0;'></div>", unsafe_allow_html=True)
            self._current_column = 0
        
        # Create a column with the specified width
        col = st.columns(width, **column_kwargs)
        self._current_column += width
        
        return col[0] if width == 1 else col
    
    def render(self, **kwargs) -> None:
        """Render the grid with the given items.
        
        Args:
            **kwargs: Additional arguments to pass to the grid container
        """
        # Apply custom CSS for the grid
        st.markdown(
            f"""
            <style>
                .grid-container-{self._id} {{
                    display: grid;
                    grid-template-columns: repeat({self.columns}, 1fr);
                    gap: {self.gap};
                    align-items: {self.vertical_align};
                    width: 100%;
                }}
                @media (max-width: 768px) {{
                    .grid-container-{self._id} {{
                        grid-template-columns: 1fr;
                    }}
                }}
            </style>
            """,
            unsafe_allow_html=True
        )
        
        # Create a container for the grid
        container = st.container()
        with container:
            st.markdown(f'<div class="grid-container-{self._id}">', unsafe_allow_html=True)
            
            # Add content using the context manager
            if 'content' in kwargs and callable(kwargs['content']):
                kwargs['content']()
                
            st.markdown('</div>', unsafe_allow_html=True)
        
        return container
