"""
This is the main entry point for the OneChain application.
It initializes the session state and renders the UI components.
"""

import streamlit as st
import logging

from src.core.analytics import LocalCSVAnalytics
from src.ui.charts import OptionsVisualization
from src.ui.sidebar import render_sidebar
from src.ui.main_content import render_main_content

# Minimal logging
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger(__name__)

def initialize_session_state():
    """Initialize session state variables."""
    defaults = {
        # Data storage
        'analytics_report': None,

        # CSV client
        'csv_client': None,
        'visualization_engine': None,

        # CSV Data
        'csv_data_loaded': False,

        # Database Browser
        'db_available_assets': [],
        'db_selected_asset': None,
        'db_available_dates': [],
        'db_selected_date': None
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Initialize engines
    if st.session_state.csv_client is None:
        st.session_state.csv_client = LocalCSVAnalytics()

    if st.session_state.visualization_engine is None:
        st.session_state.visualization_engine = OptionsVisualization()

def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="OneChain - Options Analytics",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize session state
    initialize_session_state()

    # Render sidebar
    render_sidebar()

    # Render main content
    render_main_content()