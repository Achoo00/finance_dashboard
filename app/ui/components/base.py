from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic, Type

import streamlit as st
from pydantic import BaseModel, Field

T = TypeVar('T')

class Component(ABC, Generic[T]):
    """Base class for all UI components."""
    
    def __init__(self, **kwargs):
        """Initialize the component with any properties."""
        self._id = kwargs.pop('id', None) or self.__class__.__name__.lower()
        self.class_name = kwargs.pop('class_name', '')
        self.style = kwargs.pop('style', {})
        self.kwargs = kwargs
    
    @property
    def id(self) -> str:
        """Get a unique identifier for this component."""
        return self._id
    
    @abstractmethod
    def render(self, **kwargs) -> T:
        """Render the component and return its value."""
        pass
    
    def _get_style(self) -> str:
        """Convert style dictionary to CSS string."""
        if not self.style:
            return ""
        return "; ".join(f"{k}: {v}" for k, v in self.style.items())


class StatefulComponent(Component[T], ABC):
    """Base class for components that maintain state."""
    
    def __init__(self, **kwargs):
        """Initialize with state management."""
        super().__init__(**kwargs)
        self._state_key = f"{self.id}_state"
        self._value = None
    
    @property
    def value(self) -> T:
        """Get the current value of the component."""
        if self._value is None and self._state_key in st.session_state:
            self._value = st.session_state[self._state_key]
        return self._value
    
    @value.setter
    def value(self, value: T) -> None:
        """Set the component's value and update session state."""
        self._value = value
        st.session_state[self._state_key] = value
    
    def clear(self) -> None:
        """Clear the component's value and state."""
        self._value = None
        if self._state_key in st.session_state:
            del st.session_state[self._state_key]


class ComponentContainer(Component[None]):
    """A container component that can hold other components."""
    
    def __init__(self, **kwargs):
        """Initialize the container with layout options."""
        super().__init__(**kwargs)
        self.components: List[Component] = []
        self.columns = kwargs.get('columns', 1)
    
    def add_component(self, component: Component) -> 'ComponentContainer':
        """Add a component to the container."""
        self.components.append(component)
        return self
    
    def render(self, **kwargs) -> None:
        """Render all child components."""
        if self.columns <= 1:
            for component in self.components:
                component.render(**kwargs)
        else:
            cols = st.columns(self.columns)
            for i, component in enumerate(self.components):
                with cols[i % self.columns]:
                    component.render(**kwargs)
