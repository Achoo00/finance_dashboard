"""
Theme system for the finance dashboard.

This module provides a theming system that allows for consistent styling
across the application. It includes predefined themes and the ability to
create custom themes.
"""
from enum import Enum
from typing import Dict, Any, Optional, Type, TypeVar, Generic
from pydantic import BaseModel, Field

# Type variable for theme types
T = TypeVar('T', bound='BaseTheme')

class ThemeVariant(str, Enum):
    """Available theme variants."""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"

class ColorPalette(BaseModel):
    """Color palette for a theme."""
    primary: str = "#4f46e5"
    secondary: str = "#7c3aed"
    success: str = "#10b981"
    warning: str = "#f59e0b"
    danger: str = "#ef4444"
    info: str = "#3b82f6"
    background: str = "#ffffff"
    surface: str = "#f9fafb"
    text: str = "#111827"
    text_secondary: str = "#6b7280"
    border: str = "#e5e7eb"
    shadow: str = "rgba(0, 0, 0, 0.1)"

class Spacing(BaseModel):
    """Spacing values for consistent layout."""
    xs: str = "0.25rem"
    sm: str = "0.5rem"
    md: str = "1rem"
    lg: str = "1.5rem"
    xl: str = "2rem"
    xxl: str = "3rem"

class Typography(BaseModel):
    """Typography settings for the theme."""
    font_family: str = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    font_size_base: str = "1rem"
    line_height: float = 1.5
    h1: Dict[str, str] = Field(
        default_factory=lambda: {"size": "2.5rem", "weight": "700"}
    )
    h2: Dict[str, str] = Field(
        default_factory=lambda: {"size": "2rem", "weight": "600"}
    )
    h3: Dict[str, str] = Field(
        default_factory=lambda: {"size": "1.75rem", "weight": "600"}
    )
    h4: Dict[str, str] = Field(
        default_factory=lambda: {"size": "1.5rem", "weight": "600"}
    )
    body: Dict[str, str] = Field(
        default_factory=lambda: {"size": "1rem", "weight": "400"}
    )
    small: Dict[str, str] = Field(
        default_factory=lambda: {"size": "0.875rem", "weight": "400"}
    )

class BorderRadius(BaseModel):
    """Border radius values for consistent UI elements."""
    sm: str = "0.25rem"
    md: str = "0.5rem"
    lg: str = "1rem"
    full: str = "9999px"

class BoxShadow(BaseModel):
    """Box shadow values for depth and elevation."""
    sm: str = "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
    md: str = "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
    lg: str = "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)"

class BaseTheme(BaseModel):
    """Base theme class that all themes should inherit from."""
    name: str
    variant: ThemeVariant = ThemeVariant.LIGHT
    colors: ColorPalette = Field(default_factory=ColorPalette)
    spacing: Spacing = Field(default_factory=Spacing)
    typography: Typography = Field(default_factory=Typography)
    border_radius: BorderRadius = Field(default_factory=BorderRadius)
    box_shadow: BoxShadow = Field(default_factory=BoxShadow)
    
    class Config:
        arbitrary_types_allowed = True
    
    def to_css(self) -> str:
        """Convert the theme to CSS variables."""
        css_vars = []
        
        # Add colors
        for name, value in self.colors.dict().items():
            css_vars.append(f"--color-{name}: {value};")
            
        # Add spacing
        for name, value in self.spacing.dict().items():
            css_vars.append(f"--spacing-{name}: {value};")
            
        # Add typography
        for name, value in self.typography.dict().items():
            if isinstance(value, dict):
                for prop, val in value.items():
                    css_vars.append(f"--font-{name}-{prop}: {val};")
            else:
                css_vars.append(f"--font-{name}: {value};")
                
        # Add border radius
        for name, value in self.border_radius.dict().items():
            css_vars.append(f"--radius-{name}: {value};")
            
        # Add box shadow
        for name, value in self.box_shadow.dict().items():
            css_vars.append(f"--shadow-{name}: {value};")
        
        return "\n".join(css_vars)
    
    def apply(self) -> None:
        """Apply the theme to the application."""
        import streamlit as st
        
        css = f"""
        <style>
            :root {{
                {self.to_css()}
                
                /* Component specific styles */
                .stButton>button {{
                    border-radius: var(--radius-md);
                    font-weight: 500;
                    padding: 0.5rem 1rem;
                }}
                
                .stTextInput>div>div>input, 
                .stTextArea>div>div>textarea {{
                    border-radius: var(--radius-md);
                }}
                
                .stSelectbox>div>div>div>div {{
                    border-radius: var(--radius-md);
                }}
                
                .stSlider>div>div>div>div {{
                    border-radius: var(--radius-md);
                }}
                
                .stDateInput>div>div>div>input {{
                    border-radius: var(--radius-md);
                }}
                
                .stProgress>div>div>div>div {{
                    border-radius: var(--radius-full);
                }}
                
                /* Custom scrollbar */
                ::-webkit-scrollbar {{
                    width: 8px;
                    height: 8px;
                }}
                
                ::-webkit-scrollbar-track {{
                    background: var(--color-surface);
                }}
                
                ::-webkit-scrollbar-thumb {{
                    background: var(--color-border);
                    border-radius: var(--radius-full);
                }}
                
                ::-webkit-scrollbar-thumb:hover {{
                    background: var(--color-text-secondary);
                }}
            }}
            
            /* Dark mode overrides */
            @media (prefers-color-scheme: dark) {{
                :root {{
                    --color-background: #1a1a1a;
                    --color-surface: #2d2d2d;
                    --color-text: #f5f5f5;
                    --color-text-secondary: #a0a0a0;
                    --color-border: #3d3d3d;
                    --color-shadow: rgba(0, 0, 0, 0.3);
                }}
            }}
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)

class LightTheme(BaseTheme):
    """Default light theme."""
    name: str = "light"
    variant: ThemeVariant = ThemeVariant.LIGHT
    
    def __init__(self, **data):
        super().__init__(**data)
        self.colors.primary = "#4f46e5"
        self.colors.background = "#ffffff"
        self.colors.surface = "#f9fafb"
        self.colors.text = "#111827"
        self.colors.text_secondary = "#6b7280"
        self.colors.border = "#e5e7eb"
        self.colors.shadow = "rgba(0, 0, 0, 0.1)"

class DarkTheme(BaseTheme):
    """Dark theme."""
    name: str = "dark"
    variant: ThemeVariant = ThemeVariant.DARK
    
    def __init__(self, **data):
        super().__init__(**data)
        self.colors.primary = "#6366f1"
        self.colors.background = "#1a1a1a"
        self.colors.surface = "#2d2d2d"
        self.colors.text = "#f5f5f5"
        self.colors.text_secondary = "#a0a0a0"
        self.colors.border = "#3d3d3d"
        self.colors.shadow = "rgba(0, 0, 0, 0.3)"

class ThemeManager:
    """Manages the application theme."""
    _instance = None
    _current_theme: Type[BaseTheme] = LightTheme
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_theme(cls, theme_name: Optional[str] = None) -> BaseTheme:
        """Get a theme by name."""
        themes = {
            "light": LightTheme,
            "dark": DarkTheme,
        }
        
        theme_class = themes.get(theme_name or cls._current_theme.name, cls._current_theme)
        return theme_class()
    
    @classmethod
    def set_theme(cls, theme_name: str) -> None:
        """Set the current theme."""
        themes = {
            "light": LightTheme,
            "dark": DarkTheme,
        }
        
        if theme_name in themes:
            cls._current_theme = themes[theme_name]
    
    @classmethod
    def apply_theme(cls, theme_name: Optional[str] = None) -> None:
        """Apply the specified theme or the current theme if none specified."""
        theme = cls.get_theme(theme_name)
        theme.apply()
        return theme

# Default export
theme_manager = ThemeManager()

def use_theme(theme_name: Optional[str] = None) -> BaseTheme:
    """Hook to use the current theme."""
    return theme_manager.get_theme(theme_name)

def set_theme(theme_name: str) -> None:
    """Set the current theme."""
    theme_manager.set_theme(theme_name)

def apply_theme(theme_name: Optional[str] = None) -> BaseTheme:
    """Apply the specified theme or the current theme if none specified."""
    return theme_manager.apply_theme(theme_name)
