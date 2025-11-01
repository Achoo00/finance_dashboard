from typing import Any, Dict, Optional, Union, List, Tuple
import streamlit as st
from . import use_theme

def apply_component_style(
    component: str,
    style: Dict[str, str],
    target_class: Optional[str] = None,
    parent_selector: str = ""
) -> None:
    """Apply custom styles to a Streamlit component.
    
    Args:
        component: The Streamlit component name (e.g., 'button', 'text_input')
        style: Dictionary of CSS properties and values
        target_class: Optional CSS class to target
        parent_selector: Optional parent selector for more specific targeting
    """
    selector = f".st{component.capitalize()}"
    if target_class:
        selector += f" {target_class}"
    
    if parent_selector:
        selector = f"{parent_selector} {selector}"
    
    css = f"""
    <style>
        {selector} {{
            {''.join(f"{k}: {v};" for k, v in style.items())}
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def get_color(name: str, opacity: float = 1.0) -> str:
    """Get a color from the current theme with optional opacity.
    
    Args:
        name: The color name (e.g., 'primary', 'background')
        opacity: Opacity value between 0 and 1
        
    Returns:
        The color as an rgba string
    """
    theme = use_theme()
    color = getattr(theme.colors, name, "#000000")
    
    if opacity < 1.0 and not color.startswith('rgba'):
        # Convert hex to rgba if needed
        hex_color = color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"rgba({r}, {g}, {b}, {opacity})"
    
    return color

def get_spacing(size: str) -> str:
    """Get a spacing value from the theme.
    
    Args:
        size: The size key (e.g., 'sm', 'md', 'lg')
        
    Returns:
        The spacing value as a string with units
    """
    theme = use_theme()
    return getattr(theme.spacing, size, "1rem")

def get_typography(typography_key: str, property_name: str) -> str:
    """Get a typography value from the theme.
    
    Args:
        typography_key: The typography key (e.g., 'h1', 'body')
        property_name: The property name (e.g., 'size', 'weight')
        
    Returns:
        The typography value
    """
    theme = use_theme()
    typography = getattr(theme.typography, typography_key, {})
    if isinstance(typography, dict):
        return typography.get(property_name, "")
    return ""

def get_border_radius(size: str) -> str:
    """Get a border radius value from the theme.
    
    Args:
        size: The size key (e.g., 'sm', 'md', 'lg')
        
    Returns:
        The border radius value as a string with units
    """
    theme = use_theme()
    return getattr(theme.border_radius, size, "0.25rem")

def get_box_shadow(size: str) -> str:
    """Get a box shadow value from the theme.
    
    Args:
        size: The size key (e.g., 'sm', 'md', 'lg')
        
    Returns:
        The box shadow value
    """
    theme = use_theme()
    return getattr(theme.box_shadow, size, "none")

def create_style(
    component: str,
    base_style: Dict[str, str],
    hover_style: Optional[Dict[str, str]] = None,
    active_style: Optional[Dict[str, str]] = None,
    focus_style: Optional[Dict[str, str]] = None,
    disabled_style: Optional[Dict[str, str]] = None,
) -> str:
    """Create a complete style block for a component with different states.
    
    Args:
        component: The component name
        base_style: Base styles for the component
        hover_style: Styles for hover state
        active_style: Styles for active state
        focus_style: Styles for focus state
        disabled_style: Styles for disabled state
        
    Returns:
        CSS string with all styles
    """
    selector = f".st{component.capitalize()}"
    
    css_rules = [
        f"{selector} {{\n"
        + "\n".join(f"    {k}: {v};" for k, v in base_style.items())
        + "\n}"
    ]
    
    if hover_style:
        css_rules.append(
            f"{selector}:hover {{\n"
            + "\n".join(f"    {k}: {v};" for k, v in hover_style.items())
            + "\n}"
        )
    
    if active_style:
        css_rules.append(
            f"{selector}:active {{\n"
            + "\n".join(f"    {k}: {v};" for k, v in active_style.items())
            + "\n}"
        )
    
    if focus_style:
        css_rules.append(
            f"{selector}:focus {{\n"
            + "\n".join(f"    {k}: {v};" for k, v in focus_style.items())
            + "\n}"
        )
    
    if disabled_style:
        css_rules.append(
            f"{selector}:disabled, {selector}[disabled] {{\n"
            + "\n".join(f"    {k}: {v};" for k, v in disabled_style.items())
            + "\n}"
        )
    
    return "\n".join(css_rules)

def inject_global_styles() -> None:
    """Inject global styles based on the current theme."""
    theme = use_theme()
    
    css = f"""
    <style>
        /* Base styles */
        body {{
            font-family: {font_family};
            font-size: {font_size};
            line-height: {line_height};
            color: {text_color};
            background-color: {bg_color};
        }}
        
        /* Headings */
        h1 {{
            font-size: {h1_size};
            font-weight: {h1_weight};
            margin: 0 0 {spacing_md} 0;
        }}
        
        h2 {{
            font-size: {h2_size};
            font-weight: {h2_weight};
            margin: {spacing_lg} 0 {spacing_md} 0;
        }}
        
        h3 {{
            font-size: {h3_size};
            font-weight: {h3_weight};
            margin: {spacing_md} 0 {spacing_sm} 0;
        }}
        
        /* Links */
        a {{
            color: {primary_color};
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        /* Buttons */
        .stButton > button {{
            background-color: {primary_color};
            color: white;
            border: none;
            border-radius: {border_radius_md};
            padding: {spacing_sm} {spacing_md};
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .stButton > button:hover {{
            background-color: {primary_dark};
            transform: translateY(-1px);
            box-shadow: {shadow_md};
        }}
        
        .stButton > button:active {{
            transform: translateY(0);
            box-shadow: {shadow_sm};
        }}
        
        /* Form elements */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > div > div,
        .stDateInput > div > div > div > input {{
            border: 1px solid {border_color};
            border-radius: {border_radius_md};
            padding: {spacing_sm} {spacing_md};
            font-size: {font_size};
        }}
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus,
        .stSelectbox > div > div > div > div:focus,
        .stDateInput > div > div > div > input:focus {{
            border-color: {primary_color};
            box-shadow: 0 0 0 2px {primary_color}20;
            outline: none;
        }}
        
        /* Cards */
        .card {{
            background: {surface_color};
            border-radius: {border_radius_lg};
            box-shadow: {shadow_sm};
            padding: {spacing_md};
            margin-bottom: {spacing_md};
            transition: all 0.2s ease;
        }}
        
        .card:hover {{
            box-shadow: {shadow_md};
            transform: translateY(-2px);
        }}
        
        /* Utility classes */
        .text-muted {{
            color: {text_muted};
        }}
        
        .text-center {{
            text-align: center;
        }}
        
        .mt-1 {{ margin-top: {spacing_xs}; }}
        .mt-2 {{ margin-top: {spacing_sm}; }}
        .mt-3 {{ margin-top: {spacing_md}; }}
        .mt-4 {{ margin-top: {spacing_lg}; }}
        .mt-5 {{ margin-top: {spacing_xl}; }}
        
        .mb-1 {{ margin-bottom: {spacing_xs}; }}
        .mb-2 {{ margin-bottom: {spacing_sm}; }}
        .mb-3 {{ margin-bottom: {spacing_md}; }}
        .mb-4 {{ margin-bottom: {spacing_lg}; }}
        .mb-5 {{ margin-bottom: {spacing_xl}; }}
    </style>
    """.format(
        font_family=theme.typography.font_family,
        font_size=theme.typography.font_size_base,
        line_height=theme.typography.line_height,
        text_color=theme.colors.text,
        bg_color=theme.colors.background,
        primary_color=theme.colors.primary,
        primary_dark=theme.colors.primary,
        surface_color=theme.colors.surface,
        border_color=theme.colors.border,
        text_muted=theme.colors.text_secondary,
        h1_size=theme.typography.h1["size"],
        h1_weight=theme.typography.h1["weight"],
        h2_size=theme.typography.h2["size"],
        h2_weight=theme.typography.h2["weight"],
        h3_size=theme.typography.h3["size"],
        h3_weight=theme.typography.h3["weight"],
        spacing_xs=theme.spacing.xs,
        spacing_sm=theme.spacing.sm,
        spacing_md=theme.spacing.md,
        spacing_lg=theme.spacing.lg,
        spacing_xl=theme.spacing.xl,
        border_radius_sm=theme.border_radius.sm,
        border_radius_md=theme.border_radius.md,
        border_radius_lg=theme.border_radius.lg,
        shadow_sm=theme.box_shadow.sm,
        shadow_md=theme.box_shadow.md,
    )
    
    st.markdown(css, unsafe_allow_html=True)
