"""
This module contains the sidebar UI components for the OneChain application,
including the CSV and database interfaces.
"""

import streamlit as st
import os
import logging
from typing import List

from src.core.historical import extract_asset_from_filename

logger = logging.getLogger(__name__)

def scan_folder_for_assets(folder_path: str) -> List[str]:
    """
    Scan folder and return unique asset names from snapshot files.

    Args:
        folder_path: Path to folder containing snapshot files

    Returns:
        List of unique asset names sorted alphabetically
    """
    try:
        if not os.path.exists(folder_path):
            return []

        assets = set()
        files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]

        for filename in files:
            # Look for snapshot_ prefix or any CSV with proper naming
            if filename.startswith('snapshot_'):
                # Remove snapshot_ prefix
                clean_name = filename[9:]  # Remove 'snapshot_'
                asset_name = extract_asset_from_filename(clean_name)
            else:
                # Regular CSV file
                asset_name = extract_asset_from_filename(filename)

            if asset_name and asset_name != 'unknown':
                assets.add(asset_name)

        return sorted(list(assets))

    except Exception as e:
        logger.error(f"Error scanning folder for assets: {e}")
        return []

def format_date_for_display(date_str: str) -> str:
    """Convert DDMMYY format to DD/MM/20YY for display."""
    if len(date_str) == 6 and date_str.isdigit():
        return f"{date_str[:2]}/{date_str[2:4]}/20{date_str[4:6]}"
    return date_str

def get_dates_for_asset(folder_path: str, asset_name: str) -> List[str]:
    """
    Get all available dates for specific asset, sorted newest first.

    Args:
        folder_path: Path to folder containing snapshot files
        asset_name: Asset name (e.g., 'gold1', 'crude2')

    Returns:
        List of dates in DDMMYY format, sorted newest first
    """
    try:
        if not os.path.exists(folder_path):
            return []

        dates = []
        files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]

        for filename in files:
            # Check if file belongs to this asset
            if filename.startswith('snapshot_'):
                clean_name = filename[9:]  # Remove 'snapshot_'
                file_asset = extract_asset_from_filename(clean_name)
            else:
                file_asset = extract_asset_from_filename(filename)

            if file_asset == asset_name:
                # Extract date from filename
                if filename.startswith('snapshot_'):
                    # snapshot_gold1251225.csv -> gold1251225.csv -> 251225
                    clean_name = filename[9:]
                    if len(clean_name) >= 10:  # asset + 6 digits + .csv
                        date_part = clean_name[len(asset_name):-4]  # Remove asset name and .csv
                        if len(date_part) == 6 and date_part.isdigit():
                            dates.append(date_part)
                else:
                    # gold1251225.csv -> 251225
                    if len(filename) >= 10:  # asset + 6 digits + .csv
                        date_part = filename[len(asset_name):-4]  # Remove asset name and .csv
                        if len(date_part) == 6 and date_part.isdigit():
                            dates.append(date_part)

        # Sort dates newest first (string comparison works for DDMMYY)
        return sorted(list(set(dates)), reverse=True)

    except Exception as e:
        logger.error(f"Error getting dates for asset {asset_name}: {e}")
        return []

def render_csv_interface():
    """Render CSV file upload interface."""

    # File uploader
    uploaded_file = st.file_uploader(
        "Upload CSV",
        type=['csv'],
        key="csv_uploader",
        label_visibility="collapsed"
    )

    # Load button
    if uploaded_file and st.button("🔄 Load CSV Data", type="primary", key="load_csv_button"):
        try:
            # Save uploaded file temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as temp_file:
                temp_file.write(uploaded_file.getvalue())
                temp_path = temp_file.name

            # Load data using analytics engine
            analytics = st.session_state.csv_client

            with st.spinner("Loading and analyzing CSV data..."):
                report = analytics.load_csv(temp_path, original_filename=uploaded_file.name)

            # Clean up temp file
            os.unlink(temp_path)

            if 'error' not in report:
                # Store in session state
                st.session_state.analytics_report = report
                st.session_state.csv_data_loaded = True

        except Exception as e:
            st.error(f"❌ Error loading file: {e}")


def render_database_interface():
    """Render the cascading database browser in sidebar."""

    DB_FOLDER = "historical_data"

    # Auto-scan on first load
    if not st.session_state.db_available_assets and os.path.exists(DB_FOLDER):
        st.session_state.db_available_assets = scan_folder_for_assets(DB_FOLDER)

    # Refresh button
    if st.button("🔄 Refresh Database", key="db_refresh_button"):
        if os.path.exists(DB_FOLDER):
            st.session_state.db_available_assets = scan_folder_for_assets(DB_FOLDER)
            st.session_state.db_selected_asset = None
            st.session_state.db_available_dates = []
            st.session_state.db_selected_date = None
            st.success(f"✅ Found {len(st.session_state.db_available_assets)} assets")
            st.rerun()

    # Database status
    asset_count = len(st.session_state.db_available_assets)
    st.caption(f"📊 Database: {asset_count} assets" if asset_count else "📊 Database: No snapshots found")

    # Assets dropdown
    if st.session_state.db_available_assets:
        selected_asset = st.selectbox(
            "📋 Assets:",
            options=["Select"] + st.session_state.db_available_assets,
            key="db_asset_dropdown"
        )

        if selected_asset != "Select" and selected_asset != st.session_state.db_selected_asset:
            st.session_state.db_selected_asset = selected_asset
            st.session_state.db_available_dates = get_dates_for_asset(DB_FOLDER, selected_asset)
            st.session_state.db_selected_date = None
            st.rerun()

    # Dates dropdown
    if st.session_state.db_selected_asset and st.session_state.db_available_dates:
        date_options = ["Select"] + [format_date_for_display(date) for date in st.session_state.db_available_dates]
        selected_date_display = st.selectbox("📅 Dates:", options=date_options, key="db_date_dropdown")

        if selected_date_display != "Select":
            selected_index = date_options.index(selected_date_display) - 1
            st.session_state.db_selected_date = st.session_state.db_available_dates[selected_index]

    # Load button
    if st.session_state.db_selected_asset and st.session_state.db_selected_date:
        if st.button("🔄 Load Database Entry", key="db_load_button"):
            filename = f"snapshot_{st.session_state.db_selected_asset}{st.session_state.db_selected_date}.csv"
            file_path = os.path.join(DB_FOLDER, filename)

            if os.path.exists(file_path):
                try:
                    with st.spinner("Loading and analyzing database entry..."):
                        report = st.session_state.csv_client.load_csv(file_path, original_filename=filename)

                    if 'error' not in report:
                        st.session_state.analytics_report = report
                        st.session_state.csv_data_loaded = True
                        st.success(f"✅ Loaded: {filename}")
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {report.get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Error loading file: {e}")
            else:
                st.error(f"❌ File not found: {filename}")


def render_sidebar():
    """Render the main sidebar."""
    with st.sidebar:
        # CSV Data Panel
        with st.expander("📁 CSV Data", expanded=True):
            render_csv_interface()

        # Database Panel
        with st.expander("📊 Database", expanded=False):
            render_database_interface()