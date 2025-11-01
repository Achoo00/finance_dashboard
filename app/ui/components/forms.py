"""Form components for the dashboard."""
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import date, datetime
import streamlit as st
from .base import Component

T = TypeVar('T')

@dataclass
class FormField(Generic[T]):
    """A single form field configuration."""
    key: str
    label: str
    field_type: str
    default: Optional[T] = None
    required: bool = True
    options: Optional[List[Any]] = None
    help_text: Optional[str] = None
    validate: Optional[Callable[[T], Optional[str]]] = None
    placeholder: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    format: Optional[str] = None
    disabled: bool = False
    hidden: bool = False


class Form(Component[Dict[str, Any]]):
    """A form component that handles input validation and submission."""
    
    def __init__(
        self,
        fields: List[FormField],
        submit_button_text: str = "Submit",
        clear_on_submit: bool = True,
        **kwargs
    ):
        """Initialize the form.
        
        Args:
            fields: List of form field configurations
            submit_button_text: Text for the submit button
            clear_on_submit: Whether to clear the form after submission
            **kwargs: Additional arguments for the base Component
        """
        super().__init__(**kwargs)
        self.fields = fields
        self.submit_button_text = submit_button_text
        self.clear_on_submit = clear_on_submit
        self._form_key = f"form_{id(self)}"
        self._form_data = {}
    
    def _render_field(self, field: FormField) -> None:
        """Render a single form field and handle its value.
        
        Args:
            field: The form field configuration
            
        Returns:
            The current value of the field
        """
        """Render a single form field."""
        if field.hidden:
            return
            
        field_key = f"{self._form_key}_{field.key}"
        
        # Set default value from session state if available
        if field.key in st.session_state.get(self._form_key, {}):
            field.default = st.session_state[self._form_key][field.key]
        
        # Map of field types to their corresponding Streamlit input methods
        input_methods = {
            "text": lambda: st.text_input(
                label=field.label,
                value=str(field.default) if field.default is not None else "",
                help=field.help_text,
                placeholder=field.placeholder,
                disabled=field.disabled,
                key=field_key
            ),
            "number": lambda: st.number_input(
                label=field.label,
                value=float(field.default) if field.default is not None else 0.0,
                min_value=field.min_value,
                max_value=field.max_value,
                step=field.step or 1.0,
                format=field.format or "%f",
                help=field.help_text,
                disabled=field.disabled,
                key=field_key
            ),
            "select": lambda: self._render_select_field(field, field_key, field.default),
            "multiselect": lambda: self._render_multiselect_field(field, field_key, field.default),
            "date": lambda: st.date_input(
                label=field.label,
                value=field.default if isinstance(field.default, date) else None,
                min_value=field.min_value,
                max_value=field.max_value,
                help=field.help_text,
                disabled=field.disabled,
                key=field_key
            ),
            "checkbox": lambda: st.checkbox(
                label=field.label,
                value=bool(field.default) if field.default is not None else False,
                help=field.help_text,
                disabled=field.disabled,
                key=field_key
            ),
            "slider": lambda: st.slider(
                label=field.label,
                min_value=float(field.min_value) if field.min_value is not None else 0.0,
                max_value=float(field.max_value) if field.max_value is not None else 100.0,
                value=float(field.default) if field.default is not None else 0.0,
                step=float(field.step) if field.step is not None else 1.0,
                help=field.help_text,
                disabled=field.disabled,
                key=field_key
            ),
            "textarea": lambda: st.text_area(
                label=field.label,
                value=str(field.default) if field.default is not None else "",
                help=field.help_text,
                placeholder=field.placeholder,
                disabled=field.disabled,
                key=field_key
            ),
            "time": lambda: st.time_input(
                label=field.label,
                value=field.default if isinstance(field.default, datetime.time) else None,
                help=field.help_text,
                disabled=field.disabled,
                key=field_key
            ),
            "file_uploader": lambda: st.file_uploader(
                label=field.label,
                type=field.options or None,
                help=field.help_text,
                disabled=field.disabled,
                key=field_key
            ),
            "color_picker": lambda: st.color_picker(
                label=field.label,
                value=field.default or "#000000",
                help=field.help_text,
                key=field_key
            )
        }
        
        # Render the appropriate input field
        if field.field_type in input_methods:
            value = input_methods[field.field_type]()
        else:
            st.warning(f"Unsupported field type: {field.field_type}")
            return
        
        # Store the field value
        self._form_data[field.key] = value
    
    def _render_select_field(self, field: FormField, field_key: str, current_value: Any) -> Any:
        """Render a select/dropdown field."""
        if not field.options:
            st.error(f"No options provided for select field: {field.key}")
            return None
            
        options = [opt.value if hasattr(opt, 'value') else opt for opt in field.options]
        display_options = [str(opt) for opt in options]
        
        index = 0
        if current_value is not None:
            try:
                index = options.index(current_value)
            except ValueError:
                pass
        
        selected = st.selectbox(
            label=field.label,
            options=display_options,
            index=index,
            help=field.help_text,
            disabled=field.disabled,
            key=field_key
        )
        return options[display_options.index(selected)] if selected else None
    
    def _render_multiselect_field(self, field: FormField, field_key: str, current_value: Any) -> List[Any]:
        """Render a multiselect field."""
        if not field.options:
            st.error(f"No options provided for multiselect field: {field.key}")
            return []
            
        options = [opt.value if hasattr(opt, 'value') else opt for opt in field.options]
        display_options = [str(opt) for opt in options]
        
        current_values = current_value if isinstance(current_value, list) else ([] if current_value is None else [current_value])
        default_indices = [options.index(v) for v in current_values if v in options]
        
        selected = st.multiselect(
            label=field.label,
            options=display_options,
            default=[display_options[i] for i in default_indices if i < len(display_options)],
            help=field.help_text,
            disabled=field.disabled,
            key=field_key
        )
        return [options[display_options.index(s)] for s in selected] if selected else []
    
    def _validate(self) -> bool:
        """Validate all form fields."""
        is_valid = True
        
        for field in self.fields:
            if field.hidden:
                continue
                
            value = self._form_data.get(field.key)
            
            # Check required fields
            if field.required and (value is None or value == "" or (isinstance(value, list) and not value)):
                st.error(f"{field.label} is required")
                is_valid = False
                continue
            
            # Run custom validation if provided
            if field.validate and value is not None and value != "":
                error = field.validate(value)
                if error:
                    st.error(f"{field.label}: {error}")
                    is_valid = False
        
        return is_valid
    
    def render(self) -> Dict[str, Any]:
        """Render the form and handle submission.
        
        Returns:
            A dictionary of form field values if submitted and valid, 
            otherwise an empty dictionary
        """
        with st.form(key=self._form_key):
            # Store the form data in session state for persistence
            if self._form_key not in st.session_state:
                st.session_state[self._form_key] = {}
            
            # Initialize form data with defaults
            form_data = {}
            for field in self.fields:
                if not field.hidden:
                    field_key = f"{self._form_key}_{field.key}"
                    if field_key not in st.session_state and field.default is not None:
                        st.session_state[field_key] = field.default
            
            # Render all fields
            for field in self.fields:
                if not field.hidden:
                    self._render_field(field)
            
            # Add submit button
            col1, col2 = st.columns([1, 5])
            with col1:
                submitted = st.form_submit_button(self.submit_button_text)
            
            # Handle form submission
            if submitted:
                # Get all field values
                form_data = {}
                for field in self.fields:
                    if not field.hidden:
                        field_key = f"{self._form_key}_{field.key}"
                        if field_key in st.session_state:
                            form_data[field.key] = st.session_state[field_key]
                
                # Validate required fields
                errors = {}
                for field in self.fields:
                    if field.hidden:
                        continue
                        
                    field_value = form_data.get(field.key)
                    
                    # Check required fields
                    if field.required and (field_value is None or field_value == '' or field_value == []):
                        errors[field.key] = f"{field.label} is required"
                    
                    # Run custom validation if provided
                    if field.validate and field.key in form_data:
                        error = field.validate(field_value)
                        if error:
                            errors[field.key] = error
                
                # Show validation errors if any
                if errors:
                    for error in errors.values():
                        st.error(error)
                    return {}
                
                # Clear form if needed
                if self.clear_on_submit:
                    self.clear_form()
                
                # Store the submitted data
                self._form_data = form_data
                return form_data
            
            return {}
    
    def clear_form(self) -> None:
        """Clear all form fields from session state."""
        for field in self.fields:
            field_key = f"{self._form_key}_{field.key}"
            if field_key in st.session_state:
                del st.session_state[field_key]
        if self._form_key in st.session_state:
            del st.session_state[self._form_key]


class FilterBar(Component[Dict[str, Any]]):
    """A filter/sidebar component for filtering data.
    
    This component provides a convenient way to create filter controls in a sidebar.
    It supports all the same field types as the Form component but is designed
    specifically for filtering data rather than submitting forms.
    """
    
    def __init__(
        self,
        filters: List[FormField],
        apply_button_text: str = "Apply Filters",
        reset_button_text: str = "Reset",
        auto_apply: bool = False,
        **kwargs
    ):
        """Initialize the filter bar.
        
        Args:
            filters: List of filter field configurations
            apply_button_text: Text for the apply button
            reset_button_text: Text for the reset button
            auto_apply: If True, filters are applied immediately on change
            **kwargs: Additional arguments for the base Component
        """
        super().__init__(**kwargs)
        self.filters = filters
        self.apply_button_text = apply_button_text
        self.reset_button_text = reset_button_text
        self.auto_apply = auto_apply
        self._filter_key = f"filter_{id(self)}"
        self._filter_data = {}
        
        # Initialize session state for filter values
        if self._filter_key not in st.session_state:
            st.session_state[self._filter_key] = {}
            
        # Set default values
        for field in self.filters:
            if field.default is not None and field.key not in st.session_state[self._filter_key]:
                st.session_state[self._filter_key][field.key] = field.default
    
    def _render_filter(self, field: FormField) -> None:
        """Render a single filter field.
        
        Args:
            field: The filter field configuration
        """
        if field.hidden:
            return
            
        field_key = f"{self._filter_key}_{field.key}"
        
        # Get current value from session state or use default
        current_value = st.session_state[self._filter_key].get(field.key, field.default)
        
        # Map of field types to their corresponding Streamlit input methods
        input_methods = {
            "text": lambda: st.text_input(
                label=field.label,
                value=str(current_value) if current_value is not None else "",
                help=field.help_text,
                placeholder=field.placeholder,
                disabled=field.disabled,
                key=field_key
            ),
            "number": lambda: st.number_input(
                label=field.label,
                value=float(current_value) if current_value is not None else 0.0,
                min_value=field.min_value,
                max_value=field.max_value,
                step=field.step or 1.0,
                format=field.format or "%f",
                help=field.help_text,
                disabled=field.disabled,
                key=field_key
            ),
            "select": lambda: self._render_select_field(field, field_key, current_value),
            "multiselect": lambda: self._render_multiselect_field(field, field_key, current_value),
            "date": lambda: st.date_input(
                label=field.label,
                value=current_value if isinstance(current_value, date) else None,
                min_value=field.min_value,
                max_value=field.max_value,
                help=field.help_text,
                disabled=field.disabled,
                key=field_key
            ),
            "checkbox": lambda: st.checkbox(
                label=field.label,
                value=bool(current_value) if current_value is not None else False,
                help=field.help_text,
                disabled=field.disabled,
                key=field_key
            ),
            "slider": lambda: st.slider(
                label=field.label,
                min_value=float(field.min_value) if field.min_value is not None else 0.0,
                max_value=float(field.max_value) if field.max_value is not None else 100.0,
                value=float(current_value) if current_value is not None else 0.0,
                step=float(field.step) if field.step is not None else 1.0,
                help=field.help_text,
                disabled=field.disabled,
                key=field_key
            ),
            "textarea": lambda: st.text_area(
                label=field.label,
                value=str(current_value) if current_value is not None else "",
                help=field.help_text,
                placeholder=field.placeholder,
                disabled=field.disabled,
                key=field_key
            )
        }
        
        # Render the appropriate input field
        if field.field_type in input_methods:
            value = input_methods[field.field_type]()
        else:
            st.warning(f"Unsupported filter type: {field.field_type}")
            return
        
        # Update session state with the current value
        if field_key in st.session_state:
            st.session_state[self._filter_key][field.key] = st.session_state[field_key]
    
    def _render_select_field(self, field: FormField, field_key: str, current_value: Any) -> Any:
        """Render a select/dropdown field."""
        if not field.options:
            st.error(f"No options provided for select field: {field.key}")
            return None
            
        options = [opt.value if hasattr(opt, 'value') else opt for opt in field.options]
        display_options = [str(opt) for opt in options]
        
        index = 0
        if current_value is not None:
            try:
                index = options.index(current_value)
            except ValueError:
                pass
        
        selected = st.selectbox(
            label=field.label,
            options=display_options,
            index=index,
            help=field.help_text,
            disabled=field.disabled,
            key=field_key
        )
        return options[display_options.index(selected)] if selected else None
    
    def _render_multiselect_field(self, field: FormField, field_key: str, current_value: Any) -> List[Any]:
        """Render a multiselect field."""
        if not field.options:
            st.error(f"No options provided for multiselect field: {field.key}")
            return []
            
        options = [opt.value if hasattr(opt, 'value') else opt for opt in field.options]
        display_options = [str(opt) for opt in options]
        
        current_values = current_value if isinstance(current_value, list) else ([] if current_value is None else [current_value])
        default_indices = [options.index(v) for v in current_values if v in options]
        
        selected = st.multiselect(
            label=field.label,
            options=display_options,
            default=[display_options[i] for i in default_indices if i < len(display_options)],
            help=field.help_text,
            disabled=field.disabled,
            key=field_key
        )
        return [options[display_options.index(s)] for s in selected] if selected else []
    
    def render(self) -> Dict[str, Any]:
        """Render the filter bar and return the current filter values.
        
        Returns:
            A dictionary of filter field values
        """
        with st.sidebar:
            st.header("Filters")
            
            # Render all filter fields
            for field in self.filters:
                self._render_filter(field)
            
            # Add apply/reset buttons
            col1, col2 = st.columns(2)
            with col1:
                apply_filters = st.button(self.apply_button_text, use_container_width=True)
            with col2:
                reset_filters = st.button(self.reset_button_text, use_container_width=True)
            
            # Handle reset button
            if reset_filters:
                self._reset_filters()
                st.experimental_rerun()
            
            # Get current filter values
            filter_values = self._get_filter_values()
            
            # Apply filters if auto-apply is enabled or apply button was clicked
            if apply_filters or self.auto_apply:
                return filter_values
            
            return filter_values
    
    def _reset_filters(self) -> None:
        """Reset all filter values to their defaults."""
        for field in self.filters:
            field_key = f"{self._filter_key}_{field.key}"
            if field_key in st.session_state:
                del st.session_state[field_key]
            if field.default is not None:
                st.session_state[self._filter_key][field.key] = field.default
            else:
                st.session_state[self._filter_key].pop(field.key, None)
    
    def _get_filter_values(self) -> Dict[str, Any]:
        """Get the current filter values."""
        return st.session_state.get(self._filter_key, {})
        del st.session_state[self._filter_key]
        return self._filter_data
