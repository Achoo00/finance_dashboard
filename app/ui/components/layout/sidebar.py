"""
Sidebar component for creating collapsible sidebars.

This module provides a Sidebar component that allows you to create collapsible
sidebars with various content sections.
"""
from typing import Any, Callable, Dict, List, Optional, Union
import streamlit as st
from .base import LayoutComponent


class SidebarSection:
    """A section in the sidebar that can be expanded/collapsed."""
    
    def __init__(
        self, 
        title: str, 
        content: Callable[[], None],
        expanded: bool = True,
        icon: Optional[str] = None
    ):
        """Initialize the sidebar section.
        
        Args:
            title: Title of the section
            content: Callable that renders the section content
            expanded: Whether the section is expanded by default
            icon: Optional icon to display before the title
        """
        self.title = title
        self.content = content
        self.expanded = expanded
        self.icon = icon
        self._id = f"sidebar_section_{id(self)}"


class Sidebar(LayoutComponent[None]):
    """A collapsible sidebar component.
    
    Example:
        ```python
        sidebar = Sidebar(title="My Sidebar")
        
        with sidebar:
            st.header("Section 1")
            if st.button("Click me"):
                st.write("Button clicked!")
                
            with sidebar.section("Settings", icon="⚙️"):
                setting = st.slider("Adjust setting", 0, 100, 50)
        ```
    """
    
    def __init__(
        self, 
        title: Optional[str] = None,
        width: str = "20rem",
        background_color: str = "#f0f2f6",
        **kwargs
    ):
        """Initialize the sidebar.
        
        Args:
            title: Optional title for the sidebar
            width: Width of the sidebar (CSS value)
            background_color: Background color of the sidebar
            **kwargs: Additional arguments to pass to the sidebar container
        """
        super().__init__(**kwargs)
        self.title = title
        self.width = width
        self.background_color = background_color
        self._sections: List[SidebarSection] = []
        self._container = None
    
    def section(
        self, 
        title: str, 
        content: Optional[Callable[[], None]] = None,
        expanded: bool = True,
        icon: Optional[str] = None
    ) -> 'SidebarSection':
        """Add a collapsible section to the sidebar.
        
        Args:
            title: Title of the section
            content: Optional callable that renders the section content
            expanded: Whether the section is expanded by default
            icon: Optional icon to display before the title
            
        Returns:
            The created section (can be used as a context manager)
        """
        section = SidebarSection(title, content or (lambda: None), expanded, icon)
        self._sections.append(section)
        return section
    
    def render(self, **kwargs) -> None:
        """Render the sidebar with all its sections.
        
        Args:
            **kwargs: Additional arguments to pass to the sidebar container
        """
        # Apply custom CSS for the sidebar
        st.markdown(
            f"""
            <style>
                .sidebar .sidebar-content {{
                    width: {self.width};
                    background-color: {self.background_color};
                    padding: 1rem;
                }}
                .sidebar-section {{
                    margin-bottom: 1rem;
                    border-radius: 0.5rem;
                    overflow: hidden;
                }}
                .sidebar-section-header {{
                    padding: 0.5rem 1rem;
                    background-color: #e6e9ef;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    font-weight: 600;
                }}
                .sidebar-section-header:hover {{
                    background-color: #dde0e6;
                }}
                .sidebar-section-content {{
                    padding: 0.5rem 1rem;
                }}
            </style>
            """,
            unsafe_allow_html=True
        )
        
        # Create the sidebar container
        with st.sidebar:
            if self.title:
                st.title(self.title)
            
            # Render sections
            for section in self._sections:
                # Create a container for the section
                with st.container():
                    # Section header
                    header = st.container()
                    with header:
                        col1, col2 = st.columns([1, 20])
                        with col1:
                            st.write(section.icon or "")
                        with col2:
                            st.write(section.title)
                    
                    # Section content
                    if section.expanded:
                        section.content()
    
    def __enter__(self):
        """Context manager entry point."""
        self._container = st.sidebar.container()
        return self._container.__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        if self._container:
            self._container.__exit__(exc_type, exc_val, exc_tb)
            self._container = None
