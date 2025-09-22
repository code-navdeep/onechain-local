"""
OneChain - Advanced Options Analytics Platform
Single Merged CSV Mode Only
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os
import logging
from typing import Dict, List, Optional, Any, Tuple
import math
from scipy.stats import norm
import altair as alt

# Minimal logging
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="OneChain - Options Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# INLINE CSS STYLES (CACHED)
# ============================================================================

# Cached CSS - loaded once when app starts
@st.cache_data
def get_option_table_css():
    """Return cached CSS styles for option chain table."""
    return """
/* OneChain Option Chain Table Styles */

.option-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Source Sans Pro', sans-serif;
    font-size: 14px;
    color: #1f2937;
}

.option-table th {
    background-color: #f0f2f6;
    border: 1px solid #ddd;
    padding: 10px;
    text-align: center;
    font-weight: bold;
    color: #1f2937;
    font-size: 14px;
}

.option-table td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: center;
    color: #1f2937;
    font-size: 14px;
}

/* Column Types - Base Layer */
.call-column {
    background-color: #f3f4f6;
    color: #000000;
}

.put-column {
    background-color: #f3f4f6;
    color: #000000;
}

.strike-column {
    background-color: #fbbf24;
    font-weight: bold;
}

.left-only-column {
    background-color: #dbeafe;
    color: #1e40af;
    font-weight: 500;
}

.left-only-header {
    background-color: #dbeafe !important;
    color: #1e40af !important;
}

.right-only-column {
    background-color: #dcfce7;
    color: #166534;
    font-weight: 500;
}

.right-only-header {
    background-color: #dcfce7 !important;
    color: #166534 !important;
}

/* Special Rows */
.totals-row {
    background-color: #f3f4f6;
    font-weight: bold;
    border-top: 2px solid #374151;
}

.totals-row td {
    border-top: 2px solid #374151;
}

.underlying-row {
    background: linear-gradient(to right, #eff6ff 0%, #bfdbfe 45%, #93c5fd 50%, #bfdbfe 55%, #eff6ff 100%);
    border-top: 2px solid #3b82f6;
    border-bottom: 2px solid #3b82f6;
    font-weight: bold;
}

.underlying-row td {
    border-top: 2px solid #3b82f6;
    border-bottom: 2px solid #3b82f6;
    border-left: none;
    border-right: none;
    color: #1e40af;
    background: transparent;
}

.underlying-row td.strike-column {
    background-color: #fbbf24 !important;
}

.max-pain-strike {
    border: 2px solid #8b5cf6 !important;
}

/* Value Ranking Classes */
.rank-1 {
    background-color: #16a34a !important;
    color: #ffffff !important;
    font-weight: bold !important;
}

.rank-2 {
    background-color: #f59e0b !important;
    color: #ffffff !important;
    font-weight: bold !important;
}

/* OI Change Colors */
.oi-change-up {
    color: #16a34a !important;
    font-weight: bold !important;
}

.oi-change-down {
    color: #dc2626 !important;
    font-weight: bold !important;
}

/* OI Change Extreme Borders */
.oi-change-max-increase {
    border: 3px solid #16a34a !important;
}

.oi-change-max-decrease {
    border: 3px solid #dc2626 !important;
}

/* OI Change Extreme Value Classes */
.oi-change-highest-positive {
    border: 3px solid #16a34a !important;
    font-weight: bold !important;
}

.oi-change-second-highest-positive {
    border: 2px solid #4ade80 !important;
    font-weight: normal !important;
}

.oi-change-lowest-negative {
    border: 3px solid #dc2626 !important;
    font-weight: bold !important;
}

.oi-change-second-lowest-negative {
    border: 2px solid #f87171 !important;
    font-weight: normal !important;
}

/* GEX Extreme Value Classes */
.gex-highest-positive {
    border: 3px solid #16a34a !important;
}

.gex-lowest-negative {
    border: 3px solid #dc2626 !important;
}

/* VEX Extreme Value Classes */
.vex-highest-positive {
    border: 3px solid #16a34a !important;
}

.vex-lowest-negative {
    border: 3px solid #dc2626 !important;
}

.option-table-container {
    width: 100%;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    overflow-x: auto;
    max-height: calc(100vh - 120px);
    overflow-y: auto;
    margin-bottom: 20px;
}

/* Sticky header implementation */
.option-table thead th {
    position: sticky;
    top: 0;
    background-color: #f0f2f6;
    z-index: 10;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Ensure specific header types maintain their colors with sticky positioning */
.option-table thead th.left-only-header {
    background-color: #dbeafe !important;
}

.option-table thead th.right-only-header {
    background-color: #dcfce7 !important;
}

.option-table thead th.strike-column {
    background-color: #fbbf24 !important;
}

/* Reduce bottom spacing outside the container */
.main .block-container {
    padding-bottom: 1rem !important;
    margin-bottom: 0 !important;
}

.main {
    padding-bottom: 0 !important;
    margin-bottom: 0 !important;
}

/* Target Streamlit's specific containers */
section.main > div {
    padding-bottom: 1rem !important;
}

/* Remove excessive bottom padding from Streamlit's app container */
.stApp {
    margin-bottom: 0 !important;
    padding-bottom: 0 !important;
}

/* Ensure the root container doesn't add extra space */
#root {
    margin-bottom: 0 !important;
    padding-bottom: 0 !important;
}
"""

# ============================================================================
# LOCAL CSV ANALYTICS ENGINE
# ============================================================================

class LocalCSVAnalytics:
    """
    Local CSV Options Analytics Engine.
    Loads single merged CSV files with all option data.
    """

    def __init__(self, risk_free_rate=0.065, lot_size=100):
        """Initialize CSV analytics engine."""
        self.risk_free_rate = risk_free_rate
        self.lot_size = lot_size
        logger.info(f"Initialized CSV Analytics Engine with lot_size={lot_size}")

        # Type conversion mappings
        self.type_mappings = {
            'Call': 'CE',
            'Put': 'PE'
        }

    def parse_strike_from_string(self, strike_str: str) -> Tuple[float, str]:
        """Parse strike price and option type from formatted string."""
        if not isinstance(strike_str, str):
            return float(strike_str), None

        strike_str = strike_str.strip('"').strip()

        if strike_str.endswith('C'):
            return float(strike_str[:-1].replace(',', '')), 'Call'
        elif strike_str.endswith('P'):
            return float(strike_str[:-1].replace(',', '')), 'Put'
        else:
            return float(strike_str.replace(',', '')), None

    def load_csv(self, csv_file: str, original_filename: str = None) -> Dict[str, Any]:
        """
        Load single merged CSV file and generate analytics.
        All parameters (underlying_price, expiry_date, volatility, rate) now read from CSV.

        Args:
            csv_file: Path to merged CSV file

        Returns:
            Complete analytics report dictionary
        """
        try:
            # Load CSV file
            df = pd.read_csv(csv_file)
            logger.info(f"Loaded CSV with {len(df)} rows and columns: {list(df.columns)}")

            # Extract parameters from CSV data
            parameters = self.extract_parameters_from_csv(df)
            underlying_price = parameters.get('underlying_price')
            expiry_date = parameters.get('expiry_date')
            volatility = parameters.get('volatility')
            rate = parameters.get('rate')

            if underlying_price is None:
                return {'error': 'Could not find underlying price in CSV data'}

            # Update risk-free rate if available
            if rate is not None:
                self.risk_free_rate = rate

            # Process the merged CSV data
            processed_df = self.process_merged_csv(df)

            if processed_df.empty:
                return {'error': 'No valid data after processing CSV'}

            # NEW: Asset-specific OI change tracking
            asset_name = extract_asset_from_filename(csv_file)
            logger.info(f"Processing CSV for asset: {asset_name}")

            # Add OI change tracking (auto-saves snapshot)
            try:
                tracker = HistoricalOITracker(asset_name=asset_name)
                processed_df = tracker.calculate_oi_changes(processed_df, original_df=df, original_filename=original_filename)
                logger.info(f"Added OI change tracking for {asset_name}: {len(processed_df)} options processed")
            except Exception as e:
                logger.error(f"OI tracking failed for {asset_name}: {e} - continuing without OI changes")
                # Add empty OI change columns as fallback
                processed_df['oi_change'] = 0
                processed_df['oi_change_pct'] = 0.0
                processed_df['oi_change_display'] = "ERROR"
                processed_df['oi_trend'] = "UNKNOWN"

            # Generate comprehensive analytics
            return self.generate_comprehensive_report(
                processed_df, underlying_price, expiry_date, asset_name
            )

        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            return {'error': f'Failed to load CSV: {str(e)}'}

    def extract_parameters_from_csv(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract parameters (underlying, expiry, vol, rate) from CSV data."""
        parameters = {}

        # Extract underlying price
        if 'Underlying' in df.columns:
            underlying_values = df['Underlying'].dropna()
            if not underlying_values.empty:
                # Get first non-empty value and convert to float
                underlying_str = str(underlying_values.iloc[0]).strip()
                if underlying_str and underlying_str != '':
                    try:
                        parameters['underlying_price'] = float(underlying_str)
                    except ValueError:
                        pass

        # Extract expiry date
        if 'Expiry' in df.columns:
            expiry_values = df['Expiry'].dropna()
            if not expiry_values.empty:
                expiry_str = str(expiry_values.iloc[0]).strip()
                if expiry_str and expiry_str != '':
                    parameters['expiry_date'] = expiry_str

        # Extract volatility
        if 'Vol' in df.columns:
            vol_values = df['Vol'].dropna()
            if not vol_values.empty:
                vol_str = str(vol_values.iloc[0]).strip()
                if vol_str and vol_str != '':
                    try:
                        parameters['volatility'] = float(vol_str)
                    except ValueError:
                        pass

        # Extract rate
        if 'Rate' in df.columns:
            rate_values = df['Rate'].dropna()
            if not rate_values.empty:
                rate_str = str(rate_values.iloc[0]).strip()
                if rate_str and rate_str != '':
                    try:
                        parameters['rate'] = float(rate_str)
                    except ValueError:
                        pass

        logger.info(f"Extracted parameters: {parameters}")
        return parameters

    def process_merged_csv(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process merged CSV into standard format."""
        try:
            processed = []

            for _, row in df.iterrows():
                # Parse strike and type using fixed column names
                if 'Strike' in row and 'Type' in row:
                    strike_num, parsed_type = self.parse_strike_from_string(str(row['Strike']))
                    option_type = self.type_mappings.get(row['Type'], row['Type'])

                    # Create processed row using fixed column names
                    processed_row = {
                        'strike': strike_num,
                        'option_type': option_type,
                        'last_price': self.safe_float(row.get('Last', 0)),
                        'bid_price': self.safe_float(row.get('Bid', 0)),
                        'ask_price': self.safe_float(row.get('Ask', 0)),
                        'volume': self.safe_int(row.get('Volume', 0)),
                        'oi': self.safe_int(row.get('Open Int', 0)),
                        'iv': self.parse_percentage(row.get('IV', '0%')) if 'IV' in row and pd.notna(row.get('IV')) else 0,
                        'delta': self.safe_float(row.get('Delta', 0)) if 'Delta' in row and pd.notna(row.get('Delta')) else 0,
                        'gamma': self.safe_float(row.get('Gamma', 0)) if 'Gamma' in row and pd.notna(row.get('Gamma')) else 0,
                        'theta': self.safe_float(row.get('Theta', 0)) if 'Theta' in row and pd.notna(row.get('Theta')) else 0,
                        'vega': self.safe_float(row.get('Vega', 0)) if 'Vega' in row and pd.notna(row.get('Vega')) else 0,
                        'open': self.safe_float(row.get('Open', 0)),
                        'high': self.safe_float(row.get('High', 0)),
                        'low': self.safe_float(row.get('Low', 0))
                    }

                    # Add raw values for calculations
                    processed_row['oi_raw'] = processed_row['oi']
                    processed_row['volume_raw'] = processed_row['volume']

                    processed.append(processed_row)

            result_df = pd.DataFrame(processed)
            logger.info(f"Processed merged CSV: {len(result_df)} rows")
            return result_df

        except Exception as e:
            logger.error(f"Error processing merged CSV: {e}")
            return pd.DataFrame()

    def safe_float(self, value) -> float:
        """Safely convert value to float."""
        if pd.isna(value) or value == '' or value is None:
            return 0.0
        try:
            return float(str(value).replace(',', ''))
        except:
            return 0.0

    def safe_int(self, value) -> int:
        """Safely convert value to int."""
        if pd.isna(value) or value == '' or value is None:
            return 0
        try:
            return int(float(str(value).replace(',', '')))
        except:
            return 0

    def parse_percentage(self, value) -> float:
        """Parse percentage string to float."""
        if pd.isna(value) or value == '' or value is None:
            return 0.0
        try:
            value_str = str(value).strip()
            if value_str.endswith('%'):
                return float(value_str[:-1]) / 100.0
            return float(value_str)
        except:
            return 0.0

    def generate_comprehensive_report(self, df: pd.DataFrame, underlying_price: float,
                                    expiry_date: str = None, asset_name: str = None) -> Dict[str, Any]:
        """Generate complete analytics report from processed DataFrame."""
        if df.empty:
            return {'error': 'No data available for analysis'}

        try:
            # Create enhanced dataframe with calculations
            enhanced_df = self.add_calculated_fields(df, underlying_price, expiry_date)

            # Generate analytics components
            analytics_report = {
                'asset_name': asset_name or 'unknown',  # NEW: Track which asset this report is for
                'enhanced_dataframe': enhanced_df,
                'underlying_price': underlying_price,
                'expiry_date': expiry_date,
                'total_rows': len(enhanced_df),
                'unique_strikes': enhanced_df['strike'].nunique(),
                'pcr_analysis': self.calculate_pcr_analysis(enhanced_df),
                'iv_analysis': self.calculate_iv_analysis(enhanced_df),
                'summary_stats': self.calculate_summary_stats(enhanced_df),
                'oi_change_summary': self.calculate_oi_change_summary(enhanced_df),  # NEW: OI change analytics
                'timestamp': datetime.now().isoformat()
            }

            logger.info(f"Generated analytics report with {len(enhanced_df)} options")
            return analytics_report

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {'error': f'Failed to generate analytics: {str(e)}'}

    def add_calculated_fields(self, df: pd.DataFrame, underlying_price: float,
                            expiry_date: str = None) -> pd.DataFrame:
        """Add calculated fields to the dataframe."""
        enhanced_df = df.copy()


        # Add display formatting
        enhanced_df['oi_display'] = enhanced_df['oi_raw'].apply(lambda x: f"{x/1000:.1f}K" if x >= 1000 else str(x))
        enhanced_df['volume_display'] = enhanced_df['volume_raw'].apply(lambda x: f"{x/1000:.1f}K" if x >= 1000 else str(x))


        return enhanced_df



    def calculate_pcr_analysis(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate Put-Call Ratio analysis."""
        try:
            call_data = df[df['option_type'] == 'CE']
            put_data = df[df['option_type'] == 'PE']

            call_oi = call_data['oi_raw'].sum()
            put_oi = put_data['oi_raw'].sum()
            call_volume = call_data['volume_raw'].sum()
            put_volume = put_data['volume_raw'].sum()

            pcr_oi = put_oi / call_oi if call_oi > 0 else 0
            pcr_volume = put_volume / call_volume if call_volume > 0 else 0

            return {
                'pcr_oi': pcr_oi,
                'pcr_volume': pcr_volume,
                'total_call_oi': call_oi,
                'total_put_oi': put_oi,
                'total_call_volume': call_volume,
                'total_put_volume': put_volume
            }
        except Exception as e:
            logger.error(f"Error calculating PCR: {e}")
            return {}



    def calculate_iv_analysis(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate IV analysis."""
        try:
            valid_iv = df[df['iv'] > 0]['iv']

            if valid_iv.empty:
                return {}

            return {
                'avg_iv': valid_iv.mean(),
                'median_iv': valid_iv.median(),
                'iv_min': valid_iv.min(),
                'iv_max': valid_iv.max()
            }
        except Exception as e:
            logger.error(f"Error calculating IV analysis: {e}")
            return {}

    def calculate_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate summary statistics."""
        try:
            return {
                'total_options': len(df),
                'total_calls': len(df[df['option_type'] == 'CE']),
                'total_puts': len(df[df['option_type'] == 'PE']),
                'total_oi': df['oi_raw'].sum(),
                'total_volume': df['volume_raw'].sum(),
                'avg_last_price': df[df['last_price'] > 0]['last_price'].mean(),
                'strikes_range': {
                    'min': df['strike'].min(),
                    'max': df['strike'].max()
                }
            }
        except Exception as e:
            logger.error(f"Error calculating summary stats: {e}")
            return {}

    def calculate_oi_change_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate summary statistics for OI changes."""
        try:
            # Only if we have OI change data
            if 'oi_change' not in df.columns:
                return {}

            # Separate calls and puts
            call_data = df[df['option_type'] == 'CE']
            put_data = df[df['option_type'] == 'PE']

            # Calculate totals
            total_call_oi_change = call_data['oi_change'].sum()
            total_put_oi_change = put_data['oi_change'].sum()
            net_oi_change = total_call_oi_change + total_put_oi_change

            # Count strikes with significant changes
            significant_increases = len(df[df['oi_change'] > 1000])
            significant_decreases = len(df[df['oi_change'] < -1000])

            # Find top movers
            top_increases = df.nlargest(5, 'oi_change')[['strike', 'option_type', 'oi_change', 'oi_change_pct']]
            top_decreases = df.nsmallest(5, 'oi_change')[['strike', 'option_type', 'oi_change', 'oi_change_pct']]

            return {
                'total_call_oi_change': int(total_call_oi_change),
                'total_put_oi_change': int(total_put_oi_change),
                'net_oi_change': int(net_oi_change),
                'significant_increases': significant_increases,
                'significant_decreases': significant_decreases,
                'top_increases': top_increases.to_dict('records'),
                'top_decreases': top_decreases.to_dict('records'),
                'oi_flow_direction': 'BULLISH' if net_oi_change > 1000 else 'BEARISH' if net_oi_change < -1000 else 'NEUTRAL'
            }

        except Exception as e:
            logger.error(f"Error calculating OI change summary: {e}")
            return {}

# ============================================================================
# HISTORICAL OI TRACKING
# ============================================================================

def extract_asset_from_filename(csv_file_path: str) -> str:
    """
    Extract asset name from CSV filename using DDMMYY convention.
    Handles both regular uploads and database snapshots with snapshot_ prefix.

    Examples:
        'goldoct251225.csv' -> 'goldoct'
        'snapshot_goldoct251225.csv' -> 'goldoct'
        'crude2260125.csv' -> 'crude2'
        '/path/to/ng1010225.csv' -> 'ng1'
        'irregular_name.csv' -> 'irregular_name' (fallback)

    Args:
        csv_file_path: Full path or filename of the CSV

    Returns:
        Asset name in lowercase
    """
    filename = os.path.basename(csv_file_path)
    name_without_ext = filename.replace('.csv', '')

    # Remove snapshot_ prefix if present (for database files)
    if name_without_ext.startswith('snapshot_'):
        name_without_ext = name_without_ext[9:]  # Remove 'snapshot_'

    # Check if filename follows the convention (at least 6 chars for DDMMYY)
    if len(name_without_ext) >= 6 and name_without_ext[-6:].isdigit():
        # Remove the date part (last 6 digits) to get asset name
        asset_name = name_without_ext[:-6]
        return asset_name.lower()
    else:
        # Fallback for files that don't follow the convention
        logger.warning(f"File '{filename}' doesn't follow DDMMYY convention, using full name as asset")
        return name_without_ext.lower()

class HistoricalOITracker:
    """
    Tracks daily Open Interest changes for a specific asset.

    Features:
    - Asset-specific tracking (gold1, crude2, ng1, etc.)
    - Auto-save today's snapshot (only if not already saved)
    - Calculate changes vs yesterday's data
    - Handles missing previous days gracefully
    """

    def __init__(self, asset_name: str, data_dir="historical_data"):
        """
        Initialize tracker for a specific asset.

        Args:
            asset_name: Asset identifier (e.g., 'gold1', 'crude2', 'ng1')
            data_dir: Directory to store all asset snapshots
        """
        self.asset_name = asset_name.lower()  # Normalize to lowercase
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        logger.info(f"HistoricalOITracker initialized for asset: {self.asset_name}")

    def parse_strike_from_string(self, strike_str: str) -> Tuple[float, str]:
        """Parse strike price and option type from formatted string."""
        if not isinstance(strike_str, str):
            return float(strike_str), None

        strike_str = strike_str.strip('"').strip()

        if strike_str.endswith('C'):
            return float(strike_str[:-1].replace(',', '')), 'Call'
        elif strike_str.endswith('P'):
            return float(strike_str[:-1].replace(',', '')), 'Put'
        else:
            return float(strike_str.replace(',', '')), None

    def calculate_oi_changes(self, current_df: pd.DataFrame, original_df: pd.DataFrame = None, original_filename: str = None) -> pd.DataFrame:
        """
        Calculate OI changes by comparing with yesterday's snapshot for this asset.
        Auto-saves today's snapshot if it doesn't already exist.

        Args:
            current_df: Today's processed option data for this asset

        Returns:
            DataFrame with added columns: oi_change, oi_change_pct, oi_change_display, oi_trend
        """
        try:
            # Smart lookback: Find most recent market day snapshot within 5 days
            prev_file = None
            days_searched = 0
            max_lookback_days = 5

            for days_back in range(1, max_lookback_days + 1):
                lookback_date = (datetime.now() - timedelta(days=days_back)).strftime("%d%m%y")
                candidate_snapshot = f"{self.data_dir}/snapshot_{self.asset_name}{lookback_date}.csv"

                logger.info(f"[{self.asset_name}] Checking day -{days_back}: snapshot_{self.asset_name}{lookback_date}.csv")

                if os.path.exists(candidate_snapshot):
                    prev_file = candidate_snapshot
                    days_searched = days_back
                    logger.info(f"[{self.asset_name}] Found previous market day snapshot: {os.path.basename(prev_file)} ({days_back} days ago)")
                    break

            if prev_file is None:
                logger.info(f"[{self.asset_name}] No market day snapshots found within {max_lookback_days} days - treating as first day")

                # First day or missing previous data - set changes to zero
                current_df['oi_change'] = 0
                current_df['oi_change_pct'] = 0.0
                current_df['oi_change_display'] = "-"
                current_df['oi_trend'] = "BASELINE"

            else:
                logger.info(f"[{self.asset_name}] Previous day data found - calculating OI changes")

                # Load yesterday's complete snapshot (original CSV format)
                prev_df = pd.read_csv(prev_file)
                logger.info(f"[{self.asset_name}] Loaded {len(prev_df)} previous day records")

                # Extract and rename previous day's OI data with proper mapping
                if 'Strike' in prev_df.columns and 'Type' in prev_df.columns and 'Open Int' in prev_df.columns:
                    # Original CSV format with Strike, Type, Open Int
                    prev_oi_data = prev_df[['Strike', 'Type', 'Open Int']].copy()

                    # Parse strike column properly (handles "3,655.00C" format)
                    parsed_strikes = []
                    for strike_str in prev_oi_data['Strike']:
                        strike_num, _ = self.parse_strike_from_string(str(strike_str))
                        parsed_strikes.append(strike_num)
                    prev_oi_data['strike'] = parsed_strikes

                    prev_oi_data['option_type'] = prev_oi_data['Type'].map({'Call': 'CE', 'Put': 'PE'})
                    prev_oi_data['previous_oi'] = prev_oi_data['Open Int']
                else:
                    # Fallback for processed format (shouldn't happen with new system)
                    prev_oi_data = prev_df[['strike', 'option_type', 'oi_raw']].copy()
                    prev_oi_data['previous_oi'] = prev_oi_data['oi_raw']

                # Merge current data with previous day's OI
                merged = current_df.merge(
                    prev_oi_data[['strike', 'option_type', 'previous_oi']],
                    on=['strike', 'option_type'],
                    how='left',  # Keep all current strikes, even new ones
                    suffixes=('', '')
                )

                # Handle new strikes that didn't exist yesterday
                merged['previous_oi'] = merged['previous_oi'].fillna(0)

                # Calculate absolute OI change
                merged['oi_change'] = merged['oi_raw'] - merged['previous_oi']

                # Calculate percentage change (avoid division by zero)
                merged['oi_change_pct'] = np.where(
                    merged['previous_oi'] > 0,
                    (merged['oi_change'] / merged['previous_oi']) * 100,
                    0  # New strikes or zero previous OI get 0%
                )

                # Create human-readable display strings
                merged['oi_change_display'] = merged.apply(
                    lambda row: f"+{int(row['oi_change'])}" if row['oi_change'] > 0
                               else f"{int(row['oi_change'])}" if row['oi_change'] < 0
                               else "0", axis=1
                )

                # Add trend indicators for easy filtering/highlighting
                merged['oi_trend'] = merged['oi_change'].apply(
                    lambda x: "STRONG_UP" if x > 1000
                             else "UP" if x > 0
                             else "STRONG_DOWN" if x < -1000
                             else "DOWN" if x < 0
                             else "FLAT"
                )

                # Clean up temporary column
                current_df = merged.drop('previous_oi', axis=1)

                changes_count = len(current_df[current_df['oi_change'] != 0])
                logger.info(f"[{self.asset_name}] Calculated OI changes: {changes_count} strikes with changes")

            # AUTO-SAVE: Save today's snapshot for tomorrow's comparison (only if not exists)
            # Skip if loading from database (filename already has snapshot_ prefix)
            filename_to_use = original_filename or "unknown.csv"
            if not filename_to_use.startswith("snapshot_"):
                self.save_daily_snapshot(current_df, original_filename=filename_to_use, original_df=original_df)

            return current_df

        except Exception as e:
            logger.error(f"[{self.asset_name}] Error calculating OI changes: {e}")
            # Fallback - add empty change columns so app doesn't break
            current_df['oi_change'] = 0
            current_df['oi_change_pct'] = 0.0
            current_df['oi_change_display'] = "ERROR"
            current_df['oi_trend'] = "UNKNOWN"
            return current_df

    def save_daily_snapshot(self, df: pd.DataFrame, original_filename: str = None, original_df: pd.DataFrame = None):
        """
        AUTO-SAVE complete CSV data with snapshot_ prefix naming.
        Saves as snapshot_originalname.csv format for clear identification.

        Args:
            df: Current day's processed data (not used for saving)
            original_filename: Original CSV filename (e.g., 'ng1191125.csv')
            original_df: Original CSV data with original headers (Strike, Type, Open Int, etc.)

        Returns:
            Path to snapshot file or None if error
        """
        try:
            if not original_filename:
                logger.warning(f"[{self.asset_name}] No original filename provided - skipping save")
                return None

            # Create snapshot filename with snapshot_ prefix
            snapshot_filename = f"snapshot_{original_filename}"
            file_path = f"{self.data_dir}/{snapshot_filename}"

            # CHECK: Does snapshot already exist?
            if os.path.exists(file_path):
                logger.info(f"[{self.asset_name}] Snapshot already exists: {snapshot_filename} - skipping save")
                return file_path

            # SAVE: Original CSV data with original headers for perfect compatibility
            if original_df is not None and not original_df.empty:
                # Remove any duplicates (safety check)
                snapshot = original_df.drop_duplicates()

                snapshot.to_csv(file_path, index=False)
                logger.info(f"[{self.asset_name}] AUTO-SAVED complete snapshot: {snapshot_filename} ({len(snapshot)} records, original CSV format)")
            else:
                logger.warning(f"[{self.asset_name}] No original data provided for snapshot - skipping save")
                return None

            return file_path

        except Exception as e:
            logger.error(f"[{self.asset_name}] Error saving daily snapshot: {e}")
            return None

    def get_available_dates(self) -> List[str]:
        """Get list of dates for which we have snapshots for this asset."""
        try:
            # Look for files matching this asset's pattern
            pattern = f"{self.asset_name}*.csv"
            files = [f for f in os.listdir(self.data_dir) if f.startswith(self.asset_name) and f.endswith('.csv')]

            # Extract dates (remove asset name and .csv extension)
            dates = []
            for f in files:
                date_part = f.replace(f'{self.asset_name}', '').replace('.csv', '')
                if len(date_part) == 6 and date_part.isdigit():  # Validate DDMMYY format
                    dates.append(date_part)

            return sorted(dates)

        except Exception as e:
            logger.error(f"[{self.asset_name}] Error getting available dates: {e}")
            return []

    def cleanup_old_snapshots(self, keep_days: int = 30):
        """Remove snapshots older than specified days for this asset to save disk space."""
        try:
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            cutoff_str = cutoff_date.strftime("%d%m%y")

            removed = 0
            for date_str in self.get_available_dates():
                if date_str < cutoff_str:  # String comparison works for DDMMYY format
                    file_path = f"{self.data_dir}/{self.asset_name}{date_str}.csv"
                    os.remove(file_path)
                    removed += 1

            if removed > 0:
                logger.info(f"[{self.asset_name}] Cleaned up {removed} old snapshots (older than {keep_days} days)")

        except Exception as e:
            logger.error(f"[{self.asset_name}] Error during cleanup: {e}")

# ============================================================================
# VISUALIZATION ENGINE
# ============================================================================

# Configure Altair for better performance and appearance
alt.data_transformers.enable('json')

# Chart configuration constants
CHART_TYPES = ['gex', 'iv_smile', 'oi_distribution', 'oi_change_distribution', 'volume_distribution', 'support_resistance', 'delta_distribution', 'gamma_distribution', 'vega_distribution', 'theta_distribution']

# Financial color scheme
COLORS = {
    'bullish': '#00C851',      # Green
    'bearish': '#FF4444',      # Red
    'neutral': '#33B5E5',      # Blue
    'warning': '#FF8800',      # Orange
    'background': '#1E1E1E',   # Dark background
    'text': '#FFFFFF',         # White text
    'grid': '#404040',         # Grid lines
    'call': '#00C851',         # Call options
    'put': '#FF4444',          # Put options
    'atm': '#FFBB33',          # At-the-money
    'highlight': '#AA66CC'     # Purple for highlights
}

class ChartDataManager:
    """Unified data manager for extracting chart data from analytics report."""

    def __init__(self, analytics_report: Dict[str, Any]):
        """Initialize with analytics report."""
        self.report = analytics_report
        self.df = analytics_report.get('enhanced_dataframe', pd.DataFrame())
        self.underlying_price = analytics_report.get('underlying_price', 0)
        self.available_strikes = set(self.df['strike'].unique()) if not self.df.empty else set()

    def get_gex_data(self) -> pd.DataFrame:
        """Get filtered GEX data."""
        try:
            gex_analysis = self.report.get('gex_analysis', {})
            if not gex_analysis or not self.available_strikes:
                return pd.DataFrame()

            gex_by_strike = gex_analysis.get('gex_by_strike', {})
            total_gex = gex_analysis.get('total_gex', 0)

            gex_data = []
            for strike, gex_value in gex_by_strike.items():
                if strike in self.available_strikes:  # Only filtered strikes
                    # Format GEX value same as chain table: {value:.1f}K
                    gex_formatted = f'{gex_value:.1f}K' if abs(gex_value) > 0 else '0'

                    gex_data.append({
                        'strike': strike,
                        'gex': gex_value,
                        'gex_formatted': gex_formatted,
                        'gex_abs': abs(gex_value),
                        'gex_type': 'Supportive' if gex_value > 0 else 'Resistive',
                        'distance_from_spot': abs(strike - self.underlying_price),
                        'total_gex': total_gex
                    })

            return pd.DataFrame(gex_data)
        except Exception as e:
            logger.error(f"Error extracting GEX data: {e}")
            return pd.DataFrame()

    def get_oi_distribution_data(self) -> pd.DataFrame:
        """Get OI distribution data."""
        if self.df.empty:
            return pd.DataFrame()

        try:
            oi_data = self.df.groupby(['strike', 'option_type'])['oi'].sum().reset_index()
            oi_pivot = oi_data.pivot(index='strike', columns='option_type', values='oi').fillna(0).reset_index()

            result_data = []
            for _, row in oi_pivot.iterrows():
                strike = row['strike']
                call_oi = row.get('CE', 0)
                put_oi = row.get('PE', 0)

                result_data.append({
                    'strike': strike,
                    'call_oi': call_oi,
                    'put_oi': put_oi,
                    'total_oi': call_oi + put_oi,
                    'oi_imbalance': call_oi - put_oi,
                    'distance_from_spot': abs(strike - self.underlying_price),
                    'moneyness': 'ATM' if abs(strike - self.underlying_price) < self.underlying_price * 0.02 else ('ITM' if strike < self.underlying_price else 'OTM')
                })

            return pd.DataFrame(result_data)
        except Exception as e:
            logger.error(f"Error extracting OI distribution data: {e}")
            return pd.DataFrame()

    def get_volume_distribution_data(self) -> pd.DataFrame:
        """Get volume distribution data."""
        if self.df.empty:
            return pd.DataFrame()

        try:
            volume_data = self.df.groupby(['strike', 'option_type'])['volume'].sum().reset_index()
            volume_pivot = volume_data.pivot(index='strike', columns='option_type', values='volume').fillna(0).reset_index()

            result_data = []
            for _, row in volume_pivot.iterrows():
                strike = row['strike']
                call_volume = row.get('CE', 0)
                put_volume = row.get('PE', 0)

                result_data.append({
                    'strike': strike,
                    'call_volume': call_volume,
                    'put_volume': put_volume,
                    'total_volume': call_volume + put_volume,
                    'volume_imbalance': call_volume - put_volume,
                    'distance_from_spot': abs(strike - self.underlying_price),
                    'moneyness': 'ATM' if abs(strike - self.underlying_price) < self.underlying_price * 0.02 else ('ITM' if strike < self.underlying_price else 'OTM')
                })

            return pd.DataFrame(result_data)
        except Exception as e:
            logger.error(f"Error extracting volume distribution data: {e}")
            return pd.DataFrame()

    def get_iv_smile_data(self) -> pd.DataFrame:
        """Get IV smile data."""
        if self.df.empty or 'iv' not in self.df.columns:
            return pd.DataFrame()

        try:
            iv_data = self.df[self.df['iv'] > 0].copy()
            if iv_data.empty:
                return pd.DataFrame()

            result_data = []
            for _, row in iv_data.iterrows():
                result_data.append({
                    'strike': row['strike'],
                    'option_type': row['option_type'],
                    'iv': row['iv'],
                    'distance_from_spot': abs(row['strike'] - self.underlying_price),
                    'moneyness': 'ATM' if abs(row['strike'] - self.underlying_price) < self.underlying_price * 0.02 else ('ITM' if row['strike'] < self.underlying_price else 'OTM')
                })

            return pd.DataFrame(result_data)
        except Exception as e:
            logger.error(f"Error extracting IV smile data: {e}")
            return pd.DataFrame()

    def get_oi_change_distribution_data(self) -> pd.DataFrame:
        """Get OI Change distribution data."""
        if self.df.empty or 'oi_change' not in self.df.columns:
            return pd.DataFrame()

        try:
            oi_change_data = self.df.groupby(['strike', 'option_type'])['oi_change'].sum().reset_index()
            oi_change_pivot = oi_change_data.pivot(index='strike', columns='option_type', values='oi_change').fillna(0).reset_index()

            result_data = []
            for _, row in oi_change_pivot.iterrows():
                strike = row['strike']
                call_oi_change = row.get('CE', 0)
                put_oi_change = row.get('PE', 0)

                result_data.append({
                    'strike': strike,
                    'call_oi_change': call_oi_change,
                    'put_oi_change': put_oi_change,
                    'total_oi_change': call_oi_change + put_oi_change,
                    'oi_change_imbalance': call_oi_change - put_oi_change,
                    'distance_from_spot': abs(strike - self.underlying_price),
                    'moneyness': 'ATM' if abs(strike - self.underlying_price) < self.underlying_price * 0.02 else ('ITM' if strike < self.underlying_price else 'OTM'),
                    'call_change_direction': 'Increase' if call_oi_change > 0 else ('Decrease' if call_oi_change < 0 else 'Neutral'),
                    'put_change_direction': 'Increase' if put_oi_change > 0 else ('Decrease' if put_oi_change < 0 else 'Neutral')
                })

            return pd.DataFrame(result_data)
        except Exception as e:
            logger.error(f"Error extracting OI change distribution data: {e}")
            return pd.DataFrame()

    def get_greeks_data(self, greek_name: str) -> pd.DataFrame:
        """Get Greeks data."""
        if self.df.empty or greek_name.lower() not in self.df.columns:
            return pd.DataFrame()

        try:
            greek_data = self.df[self.df[greek_name.lower()] != 0].copy()
            if greek_data.empty:
                return pd.DataFrame()

            result_data = []
            for _, row in greek_data.iterrows():
                result_data.append({
                    'strike': row['strike'],
                    'option_type': row['option_type'],
                    'greek_value': row[greek_name.lower()],
                    'distance_from_spot': abs(row['strike'] - self.underlying_price),
                    'moneyness': 'ATM' if abs(row['strike'] - self.underlying_price) < self.underlying_price * 0.02 else ('ITM' if row['strike'] < self.underlying_price else 'OTM')
                })

            return pd.DataFrame(result_data)
        except Exception as e:
            logger.error(f"Error extracting {greek_name} data: {e}")
            return pd.DataFrame()

class OptionsVisualization:
    """
    Simple chart manager - no caching, fresh renders every time.
    """

    def __init__(self):
        """Initialize visualization engine."""
        pass

    def create_gex_chart(self, analytics_report: Dict[str, Any]) -> Optional[alt.Chart]:
        """Create GEX visualization."""
        try:
            data_manager = ChartDataManager(analytics_report)
            chart_data = data_manager.get_gex_data()

            if chart_data.empty:
                return None

            gex_analysis = analytics_report.get('gex_analysis', {})

            # Base chart with zoom
            base = alt.Chart(chart_data).add_params(
                alt.selection_interval(bind='scales')
            )

            # GEX bars
            gex_bars = base.mark_bar(
                opacity=0.8,
                stroke='white',
                strokeWidth=0.5
            ).encode(
                x=alt.X('strike:O', title='Strike Price', axis=alt.Axis(labelAngle=-45)),
                y=alt.Y('gex:Q', title='Gamma Exposure (Thousands)', scale=alt.Scale(zero=True)),
                color=alt.condition(
                    alt.datum.gex > 0,
                    alt.value(COLORS['bullish']),
                    alt.value(COLORS['bearish'])
                ),
                tooltip=[
                    alt.Tooltip('strike:O', title='Strike'),
                    alt.Tooltip('gex_formatted:N', title='GEX'),
                    alt.Tooltip('gex_type:N', title='Type'),
                    alt.Tooltip('distance_from_spot:Q', title='Distance from Spot', format='.0f')
                ]
            )

            # Zero line
            zero_line = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(
                color=COLORS['text'],
                strokeWidth=1
            ).encode(y='y:Q')

            # Add underlying price line
            underlying_price_line = alt.Chart(pd.DataFrame({'x': [data_manager.underlying_price], 'label': ['Underlying']})).mark_rule(
                color=COLORS['warning'],
                strokeWidth=2,
                strokeDash=[5, 5]
            ).encode(
                x=alt.X('x:Q', scale=alt.Scale(domain=[chart_data['strike'].min(), chart_data['strike'].max()]))
            )

            chart = (gex_bars + zero_line + underlying_price_line).properties(
                width=400,
                height=400,
                title=alt.TitleParams(
                    text=f"Gamma Exposure Analysis | Total GEX: {gex_analysis.get('total_gex', 0):.1f}M",
                    fontSize=16,
                    anchor='start',
                    color=COLORS['text']
                )
            ).configure_axis(
                labelColor=COLORS['text'],
                titleColor=COLORS['text'],
                gridColor=COLORS['grid']
            ).configure_view(
                strokeWidth=0
            )

            return chart

        except Exception as e:
            logger.error(f"Error creating GEX chart: {e}")
            return None

    def create_oi_distribution_chart(self, analytics_report: Dict[str, Any]) -> Optional[alt.Chart]:
        """Create Open Interest distribution visualization."""
        try:
            data_manager = ChartDataManager(analytics_report)
            chart_data = data_manager.get_oi_distribution_data()

            if chart_data.empty:
                return None

            # Transform data for stacked bar chart
            chart_data_long = pd.melt(
                chart_data,
                id_vars=['strike', 'total_oi', 'distance_from_spot', 'moneyness'],
                value_vars=['call_oi', 'put_oi'],
                var_name='option_type',
                value_name='oi'
            )

            # Map option types to colors
            chart_data_long['color'] = chart_data_long['option_type'].map({
                'call_oi': COLORS['call'],
                'put_oi': COLORS['put']
            })

            base = alt.Chart(chart_data_long).add_params(
                alt.selection_interval(bind='scales', encodings=['x'])
            )

            # Grouped bars
            oi_bars = base.mark_bar(
                opacity=0.8,
                stroke='white',
                strokeWidth=0.5
            ).encode(
                x=alt.X('strike:O', title='Strike Price', axis=alt.Axis(labelAngle=-45)),
                y=alt.Y('oi:Q', title='Open Interest', scale=alt.Scale(type='sqrt')),
                xOffset=alt.XOffset('option_type:N'),
                color=alt.Color(
                    'option_type:N',
                    title='Option Type',
                    scale=alt.Scale(
                        domain=['call_oi', 'put_oi'],
                        range=[COLORS['call'], COLORS['put']]
                    ),
                    legend=alt.Legend(title="Option Type", titleColor=COLORS['text'], labelColor=COLORS['text'])
                ),
                tooltip=[
                    alt.Tooltip('strike:O', title='Strike'),
                    alt.Tooltip('oi:Q', title='Open Interest', format=',.0f'),
                    alt.Tooltip('option_type:N', title='Type'),
                    alt.Tooltip('moneyness:N', title='Moneyness')
                ]
            ).properties(
                width=800,
                height=400,
                title=alt.TitleParams(
                    text="Open Interest Distribution - Calls vs Puts",
                    fontSize=16,
                    anchor='start',
                    color=COLORS['text']
                )
            )

            # Add underlying price line
            underlying_price_line = alt.Chart(pd.DataFrame({'x': [data_manager.underlying_price], 'label': ['Underlying']})).mark_rule(
                color=COLORS['warning'],
                strokeWidth=2,
                strokeDash=[5, 5]
            ).encode(
                x=alt.X('x:Q', scale=alt.Scale(domain=[chart_data['strike'].min(), chart_data['strike'].max()]))
            )

            chart = (oi_bars + underlying_price_line).configure_axis(
                labelColor=COLORS['text'],
                titleColor=COLORS['text'],
                gridColor=COLORS['grid']
            ).configure_view(
                strokeWidth=0
            ).configure_legend(
                titleColor=COLORS['text'],
                labelColor=COLORS['text']
            )

            return chart

        except Exception as e:
            logger.error(f"Error creating OI distribution chart: {e}")
            return None

    def create_oi_change_distribution_chart(self, analytics_report: Dict[str, Any]) -> Optional[alt.Chart]:
        """Create OI Change distribution visualization."""
        try:
            data_manager = ChartDataManager(analytics_report)
            chart_data = data_manager.get_oi_change_distribution_data()

            if chart_data.empty:
                return None

            # Transform data for stacked bar chart with positive/negative handling
            chart_data_long = pd.melt(
                chart_data,
                id_vars=['strike', 'total_oi_change', 'distance_from_spot', 'moneyness'],
                value_vars=['call_oi_change', 'put_oi_change'],
                var_name='option_type',
                value_name='oi_change'
            )

            # Add color coding for positive/negative changes
            def get_change_color(row):
                if row['option_type'] == 'call_oi_change':
                    return COLORS['bullish'] if row['oi_change'] > 0 else COLORS['bearish']
                else:  # put_oi_change
                    return COLORS['bullish'] if row['oi_change'] > 0 else COLORS['bearish']

            chart_data_long['change_color'] = chart_data_long.apply(get_change_color, axis=1)
            chart_data_long['change_type'] = chart_data_long['oi_change'].apply(
                lambda x: 'Increase' if x > 0 else ('Decrease' if x < 0 else 'No Change')
            )

            base = alt.Chart(chart_data_long).add_params(
                alt.selection_interval(bind='scales', encodings=['x'])
            )

            # Grouped bars for OI changes
            oi_change_bars = base.mark_bar(
                opacity=0.8,
                stroke='white',
                strokeWidth=0.5
            ).encode(
                x=alt.X('strike:O', title='Strike Price', axis=alt.Axis(labelAngle=-45)),
                y=alt.Y('oi_change:Q', title='OI Change', scale=alt.Scale(zero=True)),
                xOffset=alt.XOffset('option_type:N'),
                color=alt.Color(
                    'option_type:N',
                    title='Option Type',
                    scale=alt.Scale(
                        domain=['call_oi_change', 'put_oi_change'],
                        range=[COLORS['call'], COLORS['put']]
                    ),
                    legend=alt.Legend(title="Option Type", titleColor=COLORS['text'], labelColor=COLORS['text'])
                ),
                tooltip=[
                    alt.Tooltip('strike:O', title='Strike'),
                    alt.Tooltip('oi_change:Q', title='OI Change', format='+,.0f'),
                    alt.Tooltip('option_type:N', title='Type'),
                    alt.Tooltip('change_type:N', title='Direction'),
                    alt.Tooltip('moneyness:N', title='Moneyness')
                ]
            ).properties(
                width=800,
                height=400,
                title=alt.TitleParams(
                    text="OI Change Distribution",
                    fontSize=16,
                    anchor='start',
                    color=COLORS['text']
                )
            )

            # Zero line for reference
            zero_line = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(
                color=COLORS['text'],
                strokeWidth=1,
                strokeDash=[2, 2]
            ).encode(y='y:Q')

            # Add underlying price line
            underlying_price_line = alt.Chart(pd.DataFrame({'x': [data_manager.underlying_price], 'label': ['Underlying']})).mark_rule(
                color=COLORS['warning'],
                strokeWidth=2,
                strokeDash=[5, 5]
            ).encode(
                x=alt.X('x:Q', scale=alt.Scale(domain=[chart_data['strike'].min(), chart_data['strike'].max()]))
            )

            chart = (oi_change_bars + zero_line + underlying_price_line).configure_axis(
                labelColor=COLORS['text'],
                titleColor=COLORS['text'],
                gridColor=COLORS['grid']
            ).configure_view(
                strokeWidth=0
            ).configure_legend(
                titleColor=COLORS['text'],
                labelColor=COLORS['text']
            )

            return chart

        except Exception as e:
            logger.error(f"Error creating OI change distribution chart: {e}")
            return None

    def create_volume_distribution_chart(self, analytics_report: Dict[str, Any]) -> Optional[alt.Chart]:
        """Create Volume distribution visualization."""
        try:
            data_manager = ChartDataManager(analytics_report)
            chart_data = data_manager.get_volume_distribution_data()

            if chart_data.empty:
                return None

            # Transform data for stacked bar chart
            chart_data_long = pd.melt(
                chart_data,
                id_vars=['strike', 'total_volume', 'distance_from_spot', 'moneyness'],
                value_vars=['call_volume', 'put_volume'],
                var_name='option_type',
                value_name='volume'
            )

            # Map option types to colors
            chart_data_long['color'] = chart_data_long['option_type'].map({
                'call_volume': COLORS['call'],
                'put_volume': COLORS['put']
            })

            base = alt.Chart(chart_data_long).add_params(
                alt.selection_interval(bind='scales', encodings=['x'])
            )

            # Grouped bars
            volume_bars = base.mark_bar(
                opacity=0.8,
                stroke='white',
                strokeWidth=0.5
            ).encode(
                x=alt.X('strike:O', title='Strike Price', axis=alt.Axis(labelAngle=-45)),
                y=alt.Y('volume:Q', title='Trading Volume', scale=alt.Scale(type='sqrt')),
                xOffset=alt.XOffset('option_type:N'),
                color=alt.Color(
                    'option_type:N',
                    title='Option Type',
                    scale=alt.Scale(
                        domain=['call_volume', 'put_volume'],
                        range=[COLORS['call'], COLORS['put']]
                    ),
                    legend=alt.Legend(title="Option Type", titleColor=COLORS['text'], labelColor=COLORS['text'])
                ),
                tooltip=[
                    alt.Tooltip('strike:O', title='Strike'),
                    alt.Tooltip('volume:Q', title='Volume', format=',.0f'),
                    alt.Tooltip('option_type:N', title='Type'),
                    alt.Tooltip('moneyness:N', title='Moneyness')
                ]
            ).properties(
                width=800,
                height=400,
                title=alt.TitleParams(
                    text="Volume Distribution - Calls vs Puts",
                    fontSize=16,
                    anchor='start',
                    color=COLORS['text']
                )
            )

            # Add underlying price line
            underlying_price_line = alt.Chart(pd.DataFrame({'x': [data_manager.underlying_price], 'label': ['Underlying']})).mark_rule(
                color=COLORS['warning'],
                strokeWidth=2,
                strokeDash=[5, 5]
            ).encode(
                x=alt.X('x:Q', scale=alt.Scale(domain=[chart_data['strike'].min(), chart_data['strike'].max()]))
            )

            chart = (volume_bars + underlying_price_line).configure_axis(
                labelColor=COLORS['text'],
                titleColor=COLORS['text'],
                gridColor=COLORS['grid']
            ).configure_view(
                strokeWidth=0
            ).configure_legend(
                titleColor=COLORS['text'],
                labelColor=COLORS['text']
            )

            return chart

        except Exception as e:
            logger.error(f"Error creating volume distribution chart: {e}")
            return None

    def create_iv_smile_chart(self, analytics_report: Dict[str, Any]) -> Optional[alt.Chart]:
        """Create IV smile curve visualization."""
        try:
            data_manager = ChartDataManager(analytics_report)
            chart_data = data_manager.get_iv_smile_data()

            if chart_data.empty:
                return None

            base = alt.Chart(chart_data)

            # IV smile curves - separate lines for calls and puts
            iv_lines = base.mark_line(
                point=True,
                strokeWidth=3
            ).encode(
                x=alt.X('strike:Q', title='Strike Price'),
                y=alt.Y('iv:Q', title='Implied Volatility (%)', scale=alt.Scale(zero=False)),
                color=alt.Color(
                    'option_type:N',
                    title='Option Type',
                    scale=alt.Scale(
                        domain=['CE', 'PE'],
                        range=[COLORS['call'], COLORS['put']]
                    ),
                    legend=alt.Legend(titleColor=COLORS['text'], labelColor=COLORS['text'])
                ),
                tooltip=[
                    alt.Tooltip('strike:Q', title='Strike'),
                    alt.Tooltip('iv:Q', title='IV', format='.2f'),
                    alt.Tooltip('option_type:N', title='Type'),
                    alt.Tooltip('moneyness:N', title='Moneyness')
                ]
            ).properties(
                width=600,
                height=300,
                title=alt.TitleParams(
                    text="IV Smile Curve",
                    fontSize=16,
                    anchor='start',
                    color=COLORS['text']
                )
            )

            # Add underlying price line
            underlying_price_line = alt.Chart(pd.DataFrame({'x': [data_manager.underlying_price], 'label': ['Underlying']})).mark_rule(
                color=COLORS['warning'],
                strokeWidth=2,
                strokeDash=[5, 5]
            ).encode(
                x=alt.X('x:Q')
            )

            chart = (iv_lines + underlying_price_line).configure_axis(
                labelColor=COLORS['text'],
                titleColor=COLORS['text'],
                gridColor=COLORS['grid']
            ).configure_view(
                strokeWidth=0
            ).configure_legend(
                titleColor=COLORS['text'],
                labelColor=COLORS['text']
            )

            return chart

        except Exception as e:
            logger.error(f"Error creating IV smile chart: {e}")
            return None

    def create_greek_distribution_chart(self, analytics_report: Dict[str, Any], greek_name: str) -> Optional[alt.Chart]:
        """Create Greek distribution visualization."""
        try:
            data_manager = ChartDataManager(analytics_report)
            chart_data = data_manager.get_greeks_data(greek_name)

            if chart_data.empty:
                return None

            base = alt.Chart(chart_data).add_params(
                alt.selection_interval(bind='scales', encodings=['x'])
            )

            # Calculate tight X-axis domain from actual data
            if not chart_data.empty:
                min_strike = chart_data['strike'].min()
                max_strike = chart_data['strike'].max()
                strike_padding = (max_strike - min_strike) * 0.02  # 2% padding instead of Altair's 5%
                x_domain = [min_strike - strike_padding, max_strike + strike_padding]
            else:
                x_domain = None

            # Greek distribution scatter plot
            greek_scatter = base.mark_circle(
                size=100,
                opacity=0.8,
                stroke='white',
                strokeWidth=1
            ).encode(
                x=alt.X('strike:Q', title='Strike Price', scale=alt.Scale(domain=x_domain) if x_domain else alt.Scale()),
                y=alt.Y('greek_value:Q', title=f'{greek_name.title()} Value', scale=alt.Scale(zero=False)),
                color=alt.Color(
                    'option_type:N',
                    title='Option Type',
                    scale=alt.Scale(
                        domain=['CE', 'PE'],
                        range=[COLORS['bearish'], COLORS['bullish']]  # Red for calls, Green for puts
                    ),
                    legend=alt.Legend(titleColor=COLORS['text'], labelColor=COLORS['text'])
                ),
                tooltip=[
                    alt.Tooltip('strike:Q', title='Strike'),
                    alt.Tooltip('greek_value:Q', title=f'{greek_name.title()}', format='.4f'),
                    alt.Tooltip('option_type:N', title='Type'),
                    alt.Tooltip('moneyness:N', title='Moneyness')
                ]
            ).properties(
                width=350,
                height=300,
                title=alt.TitleParams(
                    text=f"{greek_name.title()} Distribution by Strike",
                    fontSize=14,
                    anchor='start',
                    color=COLORS['text']
                )
            )

            # Add underlying price line
            underlying_price_line = alt.Chart(pd.DataFrame({'x': [data_manager.underlying_price], 'label': ['Underlying']})).mark_rule(
                color=COLORS['warning'],
                strokeWidth=2,
                strokeDash=[5, 5]
            ).encode(
                x=alt.X('x:Q', scale=alt.Scale(domain=x_domain) if x_domain else alt.Scale())
            )

            chart = (greek_scatter + underlying_price_line).configure_axis(
                labelColor=COLORS['text'],
                titleColor=COLORS['text'],
                gridColor=COLORS['grid']
            ).configure_view(
                strokeWidth=0
            ).configure_legend(
                titleColor=COLORS['text'],
                labelColor=COLORS['text']
            )

            return chart

        except Exception as e:
            logger.error(f"Error creating {greek_name} distribution chart: {e}")
            return None

    def create_support_resistance_chart(self, analytics_report: Dict[str, Any]) -> Optional[alt.Chart]:
        """Create support and resistance levels visualization."""
        try:
            data_manager = ChartDataManager(analytics_report)
            sr_data = analytics_report.get('support_resistance', {})

            if not sr_data:
                return None

            underlying_price = data_manager.underlying_price

            # Prepare support/resistance data
            levels_data = []

            # Resistance levels (from calls)
            resistance_levels = sr_data.get('resistance_levels', [])
            resistance_oi = sr_data.get('resistance_oi', [])

            for i, level in enumerate(resistance_levels[:5]):  # Top 5
                oi = resistance_oi[i] if i < len(resistance_oi) else 0
                levels_data.append({
                    'strike': level,
                    'oi': oi,
                    'level_type': 'Resistance',
                    'strength': 'Strong' if i < 2 else 'Moderate',
                    'distance_from_spot': abs(level - underlying_price) if underlying_price > 0 else 0
                })

            # Support levels (from puts)
            support_levels = sr_data.get('support_levels', [])
            support_oi = sr_data.get('support_oi', [])

            for i, level in enumerate(support_levels[:5]):  # Top 5
                oi = support_oi[i] if i < len(support_oi) else 0
                levels_data.append({
                    'strike': level,
                    'oi': oi,
                    'level_type': 'Support',
                    'strength': 'Strong' if i < 2 else 'Moderate',
                    'distance_from_spot': abs(level - underlying_price) if underlying_price > 0 else 0
                })

            if not levels_data:
                return None

            chart_data = pd.DataFrame(levels_data)

            # Create horizontal bar chart
            base = alt.Chart(chart_data)

            sr_bars = base.mark_bar(
                opacity=0.8,
                stroke='white',
                strokeWidth=1
            ).encode(
                y=alt.Y('strike:O', title='Strike Price', sort=alt.SortField('strike', order='ascending')),
                x=alt.X('oi:Q', title='Open Interest', scale=alt.Scale(type='sqrt')),
                color=alt.Color(
                    'level_type:N',
                    title='Level Type',
                    scale=alt.Scale(
                        domain=['Support', 'Resistance'],
                        range=[COLORS['bullish'], COLORS['bearish']]
                    ),
                    legend=alt.Legend(titleColor=COLORS['text'], labelColor=COLORS['text'])
                ),
                tooltip=[
                    alt.Tooltip('strike:O', title='Strike'),
                    alt.Tooltip('oi:Q', title='Open Interest', format=',.0f'),
                    alt.Tooltip('level_type:N', title='Type'),
                    alt.Tooltip('strength:N', title='Strength'),
                    alt.Tooltip('distance_from_spot:Q', title='Distance from Spot', format='.0f')
                ]
            ).properties(
                width=600,
                height=400,
                title=alt.TitleParams(
                    text="Support & Resistance Levels",
                    fontSize=16,
                    anchor='start',
                    color=COLORS['text']
                )
            )

            # Add underlying price line (horizontal since we're using horizontal bars)
            underlying_price_line = alt.Chart(pd.DataFrame({'strike': [data_manager.underlying_price], 'label': ['Underlying']})).mark_rule(
                color=COLORS['warning'],
                strokeWidth=2,
                strokeDash=[5, 5]
            ).encode(
                y=alt.Y('strike:O', sort=alt.SortField('strike', order='ascending'))
            )

            chart = (sr_bars + underlying_price_line).configure_axis(
                labelColor=COLORS['text'],
                titleColor=COLORS['text'],
                gridColor=COLORS['grid']
            ).configure_view(
                strokeWidth=0
            ).configure_legend(
                titleColor=COLORS['text'],
                labelColor=COLORS['text']
            )

            return chart

        except Exception as e:
            logger.error(f"Error creating support/resistance chart: {e}")
            return None

def setup_chart_refresh_controls() -> None:
    """Chart controls removed - no caching, always fresh."""
    pass

def get_chart_refresh_status() -> Dict[str, Any]:
    """Get current chart refresh status for debugging."""
    status = {
        'global_interval': st.session_state.get('chart_refresh_interval', 'Manual'),
        'force_update_pending': st.session_state.get('force_chart_update', False),
        'market_hours': True,  # Simplified - always considered market hours
        'chart_states': {}
    }

    for chart_type in CHART_TYPES:
        last_update = st.session_state.get(f'{chart_type}_last_update', 0)
        has_cached = f'cached_{chart_type}_chart' in st.session_state

        status['chart_states'][chart_type] = {
            'last_update': last_update,
            'time_since_update': time.time() - last_update if last_update > 0 else None,
            'has_cached_chart': has_cached,
            'individual_interval': st.session_state.get(f'{chart_type}_refresh_interval', 'Default')
        }

    return status

# ============================================================================
# DATABASE BROWSER FUNCTIONS
# ============================================================================

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

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

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

# ============================================================================
# DATA MANAGEMENT
# ============================================================================

def get_analytics_report():
    """Get the complete analytics report."""
    return st.session_state.get('analytics_report', {})

def is_data_available():
    """Check if valid data is available."""
    report = get_analytics_report()
    return bool(report and 'enhanced_dataframe' in report and not report['enhanced_dataframe'].empty)

# ============================================================================
# UI COMPONENTS
# ============================================================================


# ============================================================================
# OPTION CHAIN TABLE BUILDER
# ============================================================================

def calculate_strike_level_metrics(df: pd.DataFrame, analytics_report: Dict = None) -> Dict[float, Dict[str, float]]:
    """Calculate strike-level metrics."""
    if df.empty:
        return {}

    strike_metrics = {}
    strikes = df['strike'].unique()

    for strike in strikes:
        call_data = df[(df['strike'] == strike) & (df['option_type'] == 'CE')]
        put_data = df[(df['strike'] == strike) & (df['option_type'] == 'PE')]

        call_oi_raw = call_data['oi_raw'].iloc[0] if not call_data.empty else 0
        put_oi_raw = put_data['oi_raw'].iloc[0] if not put_data.empty else 0
        call_volume_raw = call_data['volume_raw'].iloc[0] if not call_data.empty else 0
        put_volume_raw = put_data['volume_raw'].iloc[0] if not put_data.empty else 0
        call_ltp = call_data['last_price'].iloc[0] if not call_data.empty else 0
        put_ltp = put_data['last_price'].iloc[0] if not put_data.empty else 0
        call_iv = call_data['iv'].iloc[0] if not call_data.empty else 0
        put_iv = put_data['iv'].iloc[0] if not put_data.empty else 0



        # Calculate PCR for this strike
        pcr_oi = put_oi_raw / call_oi_raw if call_oi_raw > 0 else 0
        pcr_volume = put_volume_raw / call_volume_raw if call_volume_raw > 0 else 0

        # Calculate IV spread
        iv_spread = abs(call_iv - put_iv) if call_iv > 0 and put_iv > 0 else 0

        # LTP spread
        ltp_spread = abs(call_ltp - put_ltp)

        strike_metrics[strike] = {
            'pcr_oi': pcr_oi,
            'pcr_volume': pcr_volume,
            'iv_spread': iv_spread,
            'ltp_spread': ltp_spread
        }

    return strike_metrics

def build_styled_option_chain_table(df: pd.DataFrame, underlying_price: float, analytics_report: Dict = None) -> str:
    """Build beautifully styled HTML option chain table with CSS classes and conditional formatting."""
    if df.empty:
        return "<p>No option chain data available</p>"

    try:
        # Get cached CSS (no file reading needed)
        css_content = get_option_table_css()

        # Get strike level metrics
        strike_metrics = calculate_strike_level_metrics(df, analytics_report)
        strikes = sorted(df['strike'].unique())

        # Calculate ranking for conditional formatting - separate calls and puts
        call_oi_values = []
        put_oi_values = []
        call_volume_values = []
        put_volume_values = []

        for strike in strikes:
            call_data = df[(df['strike'] == strike) & (df['option_type'] == 'CE')]
            put_data = df[(df['strike'] == strike) & (df['option_type'] == 'PE')]

            if not call_data.empty:
                call_oi_values.append((strike, call_data['oi_raw'].iloc[0]))
                call_volume_values.append((strike, call_data['volume_raw'].iloc[0]))

            if not put_data.empty:
                put_oi_values.append((strike, put_data['oi_raw'].iloc[0]))
                put_volume_values.append((strike, put_data['volume_raw'].iloc[0]))

        # Sort for ranking - separate lists for calls and puts
        call_oi_values.sort(key=lambda x: x[1], reverse=True)
        put_oi_values.sort(key=lambda x: x[1], reverse=True)
        call_volume_values.sort(key=lambda x: x[1], reverse=True)
        put_volume_values.sort(key=lambda x: x[1], reverse=True)

        # Get top 2 ranked strikes only
        top_call_oi_strikes = {x[0]: i+1 for i, x in enumerate(call_oi_values[:2])}
        top_put_oi_strikes = {x[0]: i+1 for i, x in enumerate(put_oi_values[:2])}
        top_call_volume_strikes = {x[0]: i+1 for i, x in enumerate(call_volume_values[:2])}
        top_put_volume_strikes = {x[0]: i+1 for i, x in enumerate(put_volume_values[:2])}

        # Calculate OI Change extremes (if OI change data exists)
        call_oi_change_extremes = {}
        put_oi_change_extremes = {}

        if 'oi_change' in df.columns:
            # Get OI changes for calls and puts separately
            call_oi_changes = []
            put_oi_changes = []

            for strike in strikes:
                call_data = df[(df['strike'] == strike) & (df['option_type'] == 'CE')]
                put_data = df[(df['strike'] == strike) & (df['option_type'] == 'PE')]

                if not call_data.empty:
                    call_oi_change = call_data['oi_change'].iloc[0]
                    if call_oi_change != 0:  # Only consider non-zero changes
                        call_oi_changes.append((strike, call_oi_change))

                if not put_data.empty:
                    put_oi_change = put_data['oi_change'].iloc[0]
                    if put_oi_change != 0:  # Only consider non-zero changes
                        put_oi_changes.append((strike, put_oi_change))

            # Find extremes for calls
            if call_oi_changes:
                max_call_increase = max(call_oi_changes, key=lambda x: x[1])
                min_call_decrease = min(call_oi_changes, key=lambda x: x[1])

                if max_call_increase[1] > 0:  # Positive change
                    call_oi_change_extremes[max_call_increase[0]] = 'max_increase'
                if min_call_decrease[1] < 0:  # Negative change
                    call_oi_change_extremes[min_call_decrease[0]] = 'max_decrease'

            # Find extremes for puts
            if put_oi_changes:
                max_put_increase = max(put_oi_changes, key=lambda x: x[1])
                min_put_decrease = min(put_oi_changes, key=lambda x: x[1])

                if max_put_increase[1] > 0:  # Positive change
                    put_oi_change_extremes[max_put_increase[0]] = 'max_increase'
                if min_put_decrease[1] < 0:  # Negative change
                    put_oi_change_extremes[min_put_decrease[0]] = 'max_decrease'

        # Calculate totals for underlying row display
        total_call_oi_raw = sum(x[1] for x in call_oi_values)
        total_put_oi_raw = sum(x[1] for x in put_oi_values)
        total_call_volume = sum(x[1] for x in call_volume_values)
        total_put_volume = sum(x[1] for x in put_volume_values)

        # Format totals for display
        total_call_oi = f"{total_call_oi_raw/1000:.1f}K" if total_call_oi_raw >= 1000 else str(total_call_oi_raw)
        total_put_oi = f"{total_put_oi_raw/1000:.1f}K" if total_put_oi_raw >= 1000 else str(total_put_oi_raw)

        # Calculate average IV for calls and puts
        call_iv_values = []
        put_iv_values = []
        for strike in strikes:
            call_data = df[(df['strike'] == strike) & (df['option_type'] == 'CE')]
            put_data = df[(df['strike'] == strike) & (df['option_type'] == 'PE')]

            if not call_data.empty and call_data['iv'].iloc[0] > 0:
                call_iv_values.append(call_data['iv'].iloc[0])
            if not put_data.empty and put_data['iv'].iloc[0] > 0:
                put_iv_values.append(put_data['iv'].iloc[0])

        avg_call_iv = sum(call_iv_values) / len(call_iv_values) if call_iv_values else 0
        avg_put_iv = sum(put_iv_values) / len(put_iv_values) if put_iv_values else 0

        # Calculate average PCR OI and PCR Volume across all strikes
        pcr_oi_values = []
        pcr_volume_values = []
        for strike in strikes:
            call_oi_raw = 0
            put_oi_raw = 0
            call_volume_raw = 0
            put_volume_raw = 0

            call_data = df[(df['strike'] == strike) & (df['option_type'] == 'CE')]
            put_data = df[(df['strike'] == strike) & (df['option_type'] == 'PE')]

            if not call_data.empty:
                call_oi_raw = call_data['oi_raw'].iloc[0]
                call_volume_raw = call_data['volume_raw'].iloc[0]
            if not put_data.empty:
                put_oi_raw = put_data['oi_raw'].iloc[0]
                put_volume_raw = put_data['volume_raw'].iloc[0]

            # Calculate PCR for this strike
            if call_oi_raw > 0:
                pcr_oi_values.append(put_oi_raw / call_oi_raw)
            if call_volume_raw > 0:
                pcr_volume_values.append(put_volume_raw / call_volume_raw)

        avg_pcr_oi = sum(pcr_oi_values) / len(pcr_oi_values) if pcr_oi_values else 0
        avg_pcr_volume = sum(pcr_volume_values) / len(pcr_volume_values) if pcr_volume_values else 0

        # Find highest OI values for percentage calculations
        max_call_oi = max([x[1] for x in call_oi_values]) if call_oi_values else 1
        max_put_oi = max([x[1] for x in put_oi_values]) if put_oi_values else 1

        # Calculate OI Diff and IV Skew for underlying row
        oi_diff = total_put_oi_raw - total_call_oi_raw
        iv_skew = (avg_put_iv - avg_call_iv) * 100 if (avg_put_iv > 0 and avg_call_iv > 0) else 0

        # Calculate NET OI changes for calls and puts (if OI change data exists)
        if 'oi_change' in df.columns:
            # Sum all call OI changes and put OI changes separately
            total_call_oi_change = df[df['option_type'] == 'CE']['oi_change'].sum()
            total_put_oi_change = df[df['option_type'] == 'PE']['oi_change'].sum()

            # Format for display
            net_call_oi_change = f"{int(total_call_oi_change):+}" if total_call_oi_change != 0 else "-"
            net_put_oi_change = f"{int(total_put_oi_change):+}" if total_put_oi_change != 0 else "-"
        else:
            # No OI change data available
            net_call_oi_change = "-"
            net_put_oi_change = "-"

        # Start building HTML
        html = f"""
        <style>
        {css_content}
        </style>

        <div class="option-table-container">
            <table class="option-table">
                <thead>
                    <tr>
                        <th class="left-only-header">PCR OI/Vol</th>
                        <th class="call-column">IV</th>
                        <th class="call-column">OI Chg</th>
                        <th class="call-column">OI</th>
                        <th class="call-column">Vol</th>
                        <th class="call-column">LTP</th>
                        <th class="strike-column">Strike</th>
                        <th class="put-column">LTP</th>
                        <th class="put-column">Vol</th>
                        <th class="put-column">OI</th>
                        <th class="put-column">OI Chg</th>
                        <th class="put-column">IV</th>
                    </tr>
                </thead>
                <tbody>
        """

        # Build rows - include underlying price as separate row
        all_levels = sorted(strikes + [underlying_price])

        for level in all_levels:
            if level == underlying_price:
                # Insert underlying price row with totals
                html += f"""
                    <tr class="underlying-row">
                        <td class="left-only-column">{avg_pcr_oi:.2f}<br>{avg_pcr_volume:.2f}</td>
                        <td class="call-column">{"%.1f%%" % (avg_call_iv*100) if avg_call_iv > 0 else "-"}</td>
                        <td class="call-column">{net_call_oi_change}</td>
                        <td class="call-column">{total_call_oi}<br>{(total_call_oi_raw/max_call_oi*100):.1f}%</td>
                        <td class="call-column">{total_call_volume:,}</td>
                        <td class="call-column"></td>
                        <td class="strike-column" style="font-size: 16px; font-weight: bold;">{underlying_price:.0f}<br>({oi_diff:+,.0f} | {iv_skew:+.1f}%)</td>
                        <td class="put-column"></td>
                        <td class="put-column">{total_put_volume:,}</td>
                        <td class="put-column">{total_put_oi}<br>{(total_put_oi_raw/max_put_oi*100):.1f}%</td>
                        <td class="put-column">{net_put_oi_change}</td>
                        <td class="put-column">{"%.1f%%" % (avg_put_iv*100) if avg_put_iv > 0 else "-"}</td>
                    </tr>
                """
                continue

            # Regular option strike row
            strike = level
            call_data = df[(df['strike'] == strike) & (df['option_type'] == 'CE')]
            put_data = df[(df['strike'] == strike) & (df['option_type'] == 'PE')]

            # Call side data
            call_oi_display = call_data['oi_display'].iloc[0] if not call_data.empty else "0"
            call_volume = call_data['volume_display'].iloc[0] if not call_data.empty else "0"
            call_ltp = call_data['last_price'].iloc[0] if not call_data.empty else 0
            call_iv_raw = call_data['iv'].iloc[0] if not call_data.empty else 0
            call_iv = f"{call_iv_raw*100:.1f}%" if call_iv_raw > 0 else "-"
            call_bid = call_data['bid_price'].iloc[0] if not call_data.empty else 0
            call_ask = call_data['ask_price'].iloc[0] if not call_data.empty else 0
            call_oi_raw = call_data['oi_raw'].iloc[0] if not call_data.empty else 0
            call_volume_raw = call_data['volume_raw'].iloc[0] if not call_data.empty else 0

            # Put side data
            put_oi_display = put_data['oi_display'].iloc[0] if not put_data.empty else "0"
            put_volume = put_data['volume_display'].iloc[0] if not put_data.empty else "0"
            put_ltp = put_data['last_price'].iloc[0] if not put_data.empty else 0
            put_iv_raw = put_data['iv'].iloc[0] if not put_data.empty else 0
            put_iv = f"{put_iv_raw*100:.1f}%" if put_iv_raw > 0 else "-"
            put_bid = put_data['bid_price'].iloc[0] if not put_data.empty else 0
            put_ask = put_data['ask_price'].iloc[0] if not put_data.empty else 0
            put_oi_raw = put_data['oi_raw'].iloc[0] if not put_data.empty else 0
            put_volume_raw = put_data['volume_raw'].iloc[0] if not put_data.empty else 0

            # Calculate OI percentages relative to max
            call_oi_percentage = (call_oi_raw / max_call_oi * 100) if call_oi_raw > 0 else 0
            put_oi_percentage = (put_oi_raw / max_put_oi * 100) if put_oi_raw > 0 else 0

            # Create OI display with percentages
            call_oi = f"{call_oi_display}<br>{call_oi_percentage:.1f}%"
            put_oi = f"{put_oi_display}<br>{put_oi_percentage:.1f}%"

            # Strike level metrics
            metrics = strike_metrics.get(strike, {})

            # Determine CSS classes based on ranking - separate calls/puts, top 2 only
            call_oi_class = ""
            put_oi_class = ""
            call_vol_class = ""
            put_vol_class = ""

            call_oi_rank = top_call_oi_strikes.get(strike, 0)
            put_oi_rank = top_put_oi_strikes.get(strike, 0)
            call_vol_rank = top_call_volume_strikes.get(strike, 0)
            put_vol_rank = top_put_volume_strikes.get(strike, 0)

            if call_oi_rank == 1: call_oi_class = "rank-1"
            elif call_oi_rank == 2: call_oi_class = "rank-2"

            if put_oi_rank == 1: put_oi_class = "rank-1"
            elif put_oi_rank == 2: put_oi_class = "rank-2"

            if call_vol_rank == 1: call_vol_class = "rank-1"
            elif call_vol_rank == 2: call_vol_class = "rank-2"

            if put_vol_rank == 1: put_vol_class = "rank-1"
            elif put_vol_rank == 2: put_vol_class = "rank-2"


            # Get OI change data
            call_oi_change = call_data['oi_change_display'].iloc[0] if not call_data.empty and 'oi_change_display' in call_data.columns else "-"
            put_oi_change = put_data['oi_change_display'].iloc[0] if not put_data.empty and 'oi_change_display' in put_data.columns else "-"

            # Determine OI change colors
            call_oi_change_raw = call_data['oi_change'].iloc[0] if not call_data.empty and 'oi_change' in call_data.columns else 0
            put_oi_change_raw = put_data['oi_change'].iloc[0] if not put_data.empty and 'oi_change' in put_data.columns else 0

            call_oi_change_class = "oi-change-up" if call_oi_change_raw > 0 else "oi-change-down" if call_oi_change_raw < 0 else ""
            put_oi_change_class = "oi-change-up" if put_oi_change_raw > 0 else "oi-change-down" if put_oi_change_raw < 0 else ""

            # Add extreme border classes for highest increases/decreases
            call_extreme = call_oi_change_extremes.get(strike, '')
            put_extreme = put_oi_change_extremes.get(strike, '')

            if call_extreme == 'max_increase':
                call_oi_change_class += " oi-change-max-increase"
            elif call_extreme == 'max_decrease':
                call_oi_change_class += " oi-change-max-decrease"

            if put_extreme == 'max_increase':
                put_oi_change_class += " oi-change-max-increase"
            elif put_extreme == 'max_decrease':
                put_oi_change_class += " oi-change-max-decrease"

            html += f"""
                    <tr>
                        <td class="left-only-column">{metrics.get('pcr_oi', 0):.2f}<br>{metrics.get('pcr_volume', 0):.2f}</td>
                        <td class="call-column">{call_iv}</td>
                        <td class="call-column {call_oi_change_class}">{call_oi_change}</td>
                        <td class="call-column {call_oi_class}">{call_oi}</td>
                        <td class="call-column {call_vol_class}">{call_volume}</td>
                        <td class="call-column">{call_ltp:.2f}<br>{call_bid:.2f}/{call_ask:.2f}</td>
                        <td class="strike-column">{strike:.0f}</td>
                        <td class="put-column">{put_ltp:.2f}<br>{put_bid:.2f}/{put_ask:.2f}</td>
                        <td class="put-column {put_vol_class}">{put_volume}</td>
                        <td class="put-column {put_oi_class}">{put_oi}</td>
                        <td class="put-column {put_oi_change_class}">{put_oi_change}</td>
                        <td class="put-column">{put_iv}</td>
                    </tr>
            """

        html += """
                </tbody>
            </table>
        </div>
        """

        return html

    except Exception as e:
        logger.error(f"Error building styled option chain table: {e}")
        return f"<p>Error building table: {e}</p>"

# ============================================================================
# CSV DATA LOADING
# ============================================================================

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
            pass


# ============================================================================
# SIDEBAR RENDERING
# ============================================================================

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


# ============================================================================
# MAIN CONTENT RENDERING
# ============================================================================

def render_main_content():
    """Render the unified main content - option chain table on top, analytics below."""

    if not is_data_available():
        return

    # Get data
    report = get_analytics_report()
    df = report.get('enhanced_dataframe', pd.DataFrame())
    underlying_price = report.get('underlying_price', 0)

    # === OPTION CHAIN TABLE SECTION ===
    styled_table_html = build_styled_option_chain_table(df, underlying_price, report)

    if styled_table_html and "No option chain data available" not in styled_table_html:
        st.components.v1.html(styled_table_html, height=800, scrolling=True)

    # === CHARTS SECTION ===
    if st.session_state.visualization_engine:
        viz_engine = st.session_state.visualization_engine

        # Row 1: OI Distribution | Volume Distribution
        col1, col2 = st.columns(2)
        with col1:
            fig = viz_engine.create_oi_distribution_chart(report)
            if fig:
                st.altair_chart(fig, use_container_width=True)
        with col2:
            fig = viz_engine.create_volume_distribution_chart(report)
            if fig:
                st.altair_chart(fig, use_container_width=True)

        # Check if we have IV/Greeks/OI Change data
        has_iv_data = any(df['iv'] > 0) if 'iv' in df.columns and not df.empty else False
        has_oi_change_data = any(df['oi_change'] != 0) if 'oi_change' in df.columns and not df.empty else False
        has_greeks_data = any([
            any(df[col] != 0) if col in df.columns and not df.empty else False
            for col in ['delta', 'gamma', 'theta', 'vega']
        ])

        # Row 2: OI Change Distribution | IV Smile (if data exists)
        col1, col2 = st.columns(2)
        with col1:
            if has_oi_change_data:
                fig = viz_engine.create_oi_change_distribution_chart(report)
                if fig:
                    st.altair_chart(fig, use_container_width=True)
                else:
                    st.warning("Failed to create OI Change chart")
            else:
                asset_name = report.get('asset_name', 'Unknown')
                st.info(f"OI Change chart requires previous day's data")
        with col2:
            if has_iv_data:
                fig = viz_engine.create_iv_smile_chart(report)
                if fig:
                    st.altair_chart(fig, use_container_width=True)
            else:
                st.info("IV Smile chart requires IV data")

        # Row 3: Gamma Distribution | Theta Distribution (if Greeks data exists)
        if has_greeks_data:
            col1, col2 = st.columns(2)
            with col1:
                fig = viz_engine.create_greek_distribution_chart(report, 'gamma')
                if fig:
                    st.altair_chart(fig, use_container_width=True)
            with col2:
                fig = viz_engine.create_greek_distribution_chart(report, 'theta')
                if fig:
                    st.altair_chart(fig, use_container_width=True)

            # Row 4: Vega Distribution | Delta Distribution
            col1, col2 = st.columns(2)
            with col1:
                fig = viz_engine.create_greek_distribution_chart(report, 'vega')
                if fig:
                    st.altair_chart(fig, use_container_width=True)
            with col2:
                fig = viz_engine.create_greek_distribution_chart(report, 'delta')
                if fig:
                    st.altair_chart(fig, use_container_width=True)
        else:
            st.info("Greeks distribution charts require Delta, Gamma, Theta, Vega data")

def main():
    """Main application entry point."""

    # Initialize session state
    initialize_session_state()

    # Render sidebar
    render_sidebar()

    # Render main content
    render_main_content()

    # No auto-refresh needed for static CSV files

if __name__ == "__main__":
    main()