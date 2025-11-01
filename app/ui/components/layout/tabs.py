"""
Tabs component for organizing content into multiple panels.

This module provides a Tabs component that allows you to create tabbed interfaces
where users can switch between different content panels.
"""
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
import streamlit as st
from .base import LayoutComponent

class Tab:
    """A single tab in a Tabs component."""
    
    def __init__(
        self, 
        label: str, 
        content: Callable[[], None],
        icon: Optional[str] = None,
        disabled: bool = False
    ):
        """Initialize the tab.
        
        Args:
            label: Display label for the tab
            content: Callable that renders the tab content
            icon: Optional icon to display before the label
            disabled: Whether the tab is disabled
        """
        self.label = label
        self.content = content
        self.icon = icon
        self.disabled = disabled
        self._id = id(self)


class Tabs(LayoutComponent[Optional[int]]):
    """A tabs component for organizing content into multiple panels.
    
    Example:
        ```python
        tabs = Tabs()
        tabs.add_tab("Tab 1", lambda: st.write("Content 1"))
        tabs.add_tab("Tab 2", lambda: st.write("Content 2"))
        selected_tab = tabs.render()
        ```
    """
    
    def __init__(
        self, 
        tabs: Optional[List[Tab]] = None,
        default_index: int = 0,
        **kwargs
    ):
        """Initialize the tabs component.
        
        Args:
            tabs: Optional list of Tab objects
            default_index: Index of the initially selected tab
            **kwargs: Additional arguments to pass to the tabs container
        """
        super().__init__(**kwargs)
        self.tabs = tabs or []
        self.default_index = default_index
        self._selected_index = default_index
    
    def add_tab(
        self, 
        label: str, 
        content: Callable[[], None],
        icon: Optional[str] = None,
        disabled: bool = False
    ) -> 'Tabs':
        """Add a new tab to the tabs component.
        
        Args:
            label: Display label for the tab
            content: Callable that renders the tab content
            icon: Optional icon to display before the label
            disabled: Whether the tab is disabled
            
        Returns:
            Self for method chaining
        """
        self.tabs.append(Tab(label, content, icon, disabled))
        return self
    
    def render(self, **kwargs) -> Optional[int]:
        """Render the tabs component.
        
        Args:
            **kwargs: Additional arguments to pass to the tabs container
            
        Returns:
            Index of the selected tab, or None if no tabs
        """
        if not self.tabs:
            return None
            
        # Create tab labels with optional icons
        tab_labels = []
        for tab in self.tabs:
            label = tab.label
            if tab.icon:
                label = f"{tab.icon} {label}"
            if tab.disabled:
                label = f"🔒 {label}"
            tab_labels.append(label)
        
        # Create tabs
        tab_objects = st.tabs(tab_labels, **kwargs)
        
        # Determine selected tab
        for i, tab in enumerate(self.tabs):
            if not tab.disabled and i == self.default_index:
                with tab_objects[i]:
                    tab.content()
                self._selected_index = i
                break
        
        return self._selected_index
    
    @property
    def selected_index(self) -> Optional[int]:
        """Get the index of the currently selected tab."""
        return self._selected_index if self.tabs else None
    
    @property
    def selected_tab(self) -> Optional[Tab]:
        """Get the currently selected tab."""
        if not self.tabs or self._selected_index is None:
            return None
        return self.tabs[self._selected_index]
