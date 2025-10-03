"""
This module handles historical data tracking, including Open Interest (OI) changes.
"""

import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple

logger = logging.getLogger(__name__)

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