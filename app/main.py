import logging
import sys
from pathlib import Path

import streamlit as st

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Configure logging before other imports
from app.config.logging_config import setup_logging
from app.config.settings import settings
from app.database.session import init_db

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)


def setup_page_config() -> None:
    """Configure the Streamlit page settings."""
    st.set_page_config(
        page_title=settings.APP_NAME,
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS
    st.markdown(
        """
        <style>
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            .sidebar .sidebar-content {
                background-color: #f8f9fa;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_sidebar() -> None:
    """Render the application sidebar."""
    st.sidebar.title(settings.APP_NAME)
    st.sidebar.markdown("---")
    
    # Navigation
    st.sidebar.subheader("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Dashboard", "Portfolios", "Markets", "Settings"],
        index=0,
    )
    
    # Display app info
    st.sidebar.markdown("---")
    st.sidebar.info(
        f"Finance Dashboard v{settings.VERSION}\\n        Environment: {settings.ENVIRONMENT}"
    )
    
    return page


def main() -> None:
    """Main application function."""
    try:
        # Initialize database
        init_db()
        
        # Setup page config
        setup_page_config()
        
        # Show sidebar and get current page
        current_page = show_sidebar()
        
        # Display page content based on selection
        if current_page == "Dashboard":
            st.title("📊 Dashboard")
            st.write("Welcome to your financial dashboard!")
            
            # Add some sample content
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Portfolio Value", "$12,345.67", "+2.5%")
            with col2:
                st.metric("Today's Change", "+$123.45", "+1.0%")
                
            st.write("### Recent Activity")
            st.write("Your recent transactions and portfolio updates will appear here.")
            
        elif current_page == "Portfolios":
            st.title("📈 Portfolios")
            st.write("Manage your investment portfolios.")
            
        elif current_page == "Markets":
            st.title("📈 Markets")
            st.write("Market data and analysis.")
            
        elif current_page == "Settings":
            st.title("⚙️ Settings")
            st.write("Application settings and preferences.")
            
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        st.error("An unexpected error occurred. Please check the logs for details.")


if __name__ == "__main__":
    main()
