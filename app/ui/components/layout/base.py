"""Base layout components for the application."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
import streamlit as st

T = TypeVar('T')

class LayoutComponent(Generic[T], ABC):
    """Base class for all layout components."""
    
    def __init__(self, **kwargs):
        """Initialize the layout component.
        
        Args:
            **kwargs: Additional arguments to pass to the component
        """
        self._id = id(self)
        self.kwargs = kwargs
    
    @abstractmethod
    def render(self, **kwargs) -> T:
        """Render the layout component.
        
        Returns:
            The rendered component's return value
        """
        pass
    
    def __call__(self, **kwargs):
        """Make the component callable."""
        return self.render(**kwargs)
