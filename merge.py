#!/usr/bin/env python3
"""
Generic CSV Merger for Options Data

COMMAND LINE USAGE:
    python3 csv_merger.py <prices_file> <greeks_file> <output_file>

DESCRIPTION:
    This script merges two CSV files containing options data:
    - Prices file: Contains pricing data with strikes like "3,305.00C"
    - Greeks file: Contains Greeks data with separate Strike and Type columns
    - Only keeps strikes that exist in BOTH files (removes non-overlapping strikes)
    - Removes 'Last Trade' column completely from output

REQUIREMENTS:
    - Prices file must have Strike column with format like "3,305.00C", "3,310.00P"
    - Greeks file must have Strike column with format like "3,305.00" and separate Type column
    - Both files must be valid CSV format

EXAMPLES:
    # Basic usage with current files
    python3 csv_merger.py gcv25-prices.csv gcv25-greeks.csv gcv25-final.csv

    # Future usage with other assets
    python3 csv_merger.py aapl-prices.csv aapl-greeks.csv aapl-merged.csv
    python3 csv_merger.py tsla-prices.csv tsla-greeks.csv tsla-merged.csv
    python3 csv_merger.py spy-prices.csv spy-greeks.csv spy-merged.csv

    # Works with any similarly patterned CSV files
    python3 csv_merger.py prices_data.csv greeks_data.csv final_output.csv

OUTPUT:
    - CSV file containing only strikes present in BOTH input files
    - Essential pricing columns (Last, Bid, Ask, Volume, Open Int)
    - All Greeks columns (IV, Delta, Gamma, Theta, Vega) with normalized precision
    - 1 empty column for manual population (underlying)
    - No 'Last Trade' column (removed completely)
    - Rows sorted by strike price and option type
"""

import pandas as pd
import sys
import os

def extract_strike_and_type(strike_str):
    """Extract numeric strike and option type from strike string"""
    strike_str = str(strike_str).strip('"').strip()

    if strike_str.endswith('C'):
        return float(strike_str[:-1].replace(',', '')), 'Call'
    elif strike_str.endswith('P'):
        return float(strike_str[:-1].replace(',', '')), 'Put'
    else:
        # For greeks file format like "3,310.00"
        return float(strike_str.replace(',', '')), None

def merge_csv_files(prices_file, greeks_file, output_file):
    """
    Merge two CSV files with options data

    Args:
        prices_file: Path to CSV with pricing data
        greeks_file: Path to CSV with Greeks data
        output_file: Path for merged output CSV
    """

    print(f"Step 1: Reading input files...")
    print(f"  Prices file: {prices_file}")
    print(f"  Greeks file: {greeks_file}")

    # Check if files exist
    if not os.path.exists(prices_file):
        raise FileNotFoundError(f"Prices file not found: {prices_file}")
    if not os.path.exists(greeks_file):
        raise FileNotFoundError(f"Greeks file not found: {greeks_file}")

    # Read the CSV files
    prices_df = pd.read_csv(prices_file)
    greeks_df = pd.read_csv(greeks_file)

    print(f"  Prices file has {len(prices_df)} rows")
    print(f"  Greeks file has {len(greeks_df)} rows")

    print(f"\nStep 2: Processing strikes to identify common ones...")

    # Process prices data
    prices_processed = []
    for _, row in prices_df.iterrows():
        try:
            strike_num, option_type = extract_strike_and_type(row['Strike'])
            row_dict = row.to_dict()
            row_dict['strike_num'] = strike_num
            row_dict['option_type'] = option_type
            prices_processed.append(row_dict)
        except Exception as e:
            print(f"  Warning: Could not process prices row with Strike={row['Strike']}: {e}")

    # Process greeks data
    greeks_processed = []
    for _, row in greeks_df.iterrows():
        try:
            strike_num, _ = extract_strike_and_type(row['Strike'])
            row_dict = row.to_dict()
            row_dict['strike_num'] = strike_num
            row_dict['option_type'] = row['Type']
            greeks_processed.append(row_dict)
        except Exception as e:
            print(f"  Warning: Could not process greeks row with Strike={row['Strike']}: {e}")

    # Create lookup sets for common strikes
    prices_keys = {(row['strike_num'], row['option_type']) for row in prices_processed}
    greeks_keys = {(row['strike_num'], row['option_type']) for row in greeks_processed}

    # Find ONLY common strikes (intersection)
    common_keys = prices_keys & greeks_keys
    only_in_prices = prices_keys - greeks_keys
    only_in_greeks = greeks_keys - prices_keys

    print(f"  Common strikes (keeping): {len(common_keys)}")
    print(f"  Only in prices (removing): {len(only_in_prices)} - {only_in_prices}")
    print(f"  Only in greeks (removing): {len(only_in_greeks)} - {only_in_greeks}")

    print(f"\nStep 3: Creating merged dataset with only common strikes...")

    # Create lookup dictionaries
    prices_lookup = {(row['strike_num'], row['option_type']): row for row in prices_processed}
    greeks_lookup = {(row['strike_num'], row['option_type']): row for row in greeks_processed}

    merged_rows = []

    # Only process common strikes
    for strike_num, option_type in sorted(common_keys):
        merged_row = {}

        # Get prices data
        prices_data = prices_lookup[(strike_num, option_type)]
        merged_row.update(prices_data)

        # Get greeks data
        greeks_data = greeks_lookup[(strike_num, option_type)]

        # Add greeks-specific columns
        for col in ['IV', 'Delta', 'Gamma', 'Theta', 'Vega', 'IV Skew']:
            if col in greeks_data:
                merged_row[col] = greeks_data[col]

        # Handle overlapping columns (prefer prices data for 'Last')
        if 'Last' not in merged_row and 'Last' in greeks_data:
            merged_row['Last'] = greeks_data['Last']

        # Clean up helper columns
        if 'strike_num' in merged_row:
            del merged_row['strike_num']
        if 'option_type' in merged_row:
            del merged_row['option_type']

        merged_rows.append(merged_row)

    print(f"Step 4: Creating final DataFrame with {len(merged_rows)} rows...")

    merged_df = pd.DataFrame(merged_rows)

    # Remove 'Last Trade' column completely if it exists
    if 'Last Trade' in merged_df.columns:
        merged_df = merged_df.drop('Last Trade', axis=1)
        print(f"  Removed 'Last Trade' column")

    # Add 1 new empty column for manual population
    merged_df['Underlying'] = ''
    print(f"  Added 1 empty column: Underlying")

    # Normalize Greeks to specified decimal places
    if 'Delta' in merged_df.columns:
        merged_df['Delta'] = merged_df['Delta'].apply(lambda x: f"{float(x):.2f}" if pd.notna(x) and x != '' else x)
    if 'Theta' in merged_df.columns:
        merged_df['Theta'] = merged_df['Theta'].apply(lambda x: f"{float(x):.2f}" if pd.notna(x) and x != '' else x)
    if 'Vega' in merged_df.columns:
        merged_df['Vega'] = merged_df['Vega'].apply(lambda x: f"{float(x):.2f}" if pd.notna(x) and x != '' else x)
    if 'Gamma' in merged_df.columns:
        merged_df['Gamma'] = merged_df['Gamma'].apply(lambda x: f"{float(x):.4f}" if pd.notna(x) and x != '' else x)
    print(f"  Normalized Greeks: Delta/Theta/Vega to 2 decimals, Gamma to 4 decimals")

    # Reorder columns logically - removed unused columns
    preferred_order = ['Strike', 'Type', 'Last', 'Bid', 'Ask', 'Volume', 'Open Int',
                      'IV', 'Delta', 'Gamma', 'Theta', 'Vega', 'Underlying']

    # Only include columns that exist
    final_columns = [col for col in preferred_order if col in merged_df.columns]
    remaining_columns = [col for col in merged_df.columns if col not in final_columns]
    merged_df = merged_df[final_columns + remaining_columns]

    print(f"Step 5: Saving merged file to {output_file}...")
    merged_df.to_csv(output_file, index=False)

    print(f"✅ Success! Merged file saved with:")
    print(f"  - {len(merged_df)} rows (only common strikes)")
    print(f"  - {len(merged_df.columns)} columns")
    print(f"  - Columns: {list(merged_df.columns)}")

    return merged_df

def main():
    if len(sys.argv) != 4:
        print("Usage: python csv_merger.py <prices_file> <greeks_file> <output_file>")
        print("\nExample:")
        print("  python csv_merger.py gcv25-prices.csv gcv25-greeks.csv gcv25-final.csv")
        sys.exit(1)

    prices_file = sys.argv[1]
    greeks_file = sys.argv[2]
    output_file = sys.argv[3]

    try:
        merged_df = merge_csv_files(prices_file, greeks_file, output_file)
        print(f"\n🎉 Merge completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()