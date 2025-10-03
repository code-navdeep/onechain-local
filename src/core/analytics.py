"""
This module contains the core analytics engine for the OneChain application.
"""

import pandas as pd
import logging
from datetime import datetime
from typing import Dict, Any, Tuple

from .historical import HistoricalOITracker, extract_asset_from_filename

logger = logging.getLogger(__name__)

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