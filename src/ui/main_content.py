"""
This module is responsible for rendering the main content of the OneChain application,
including the option chain table and analytics charts.
"""

import streamlit as st
import pandas as pd
import logging
from typing import Dict, Any

from src.ui.styles import get_option_table_css

logger = logging.getLogger(__name__)

def is_data_available():
    """Check if valid data is available in the session state."""
    report = st.session_state.get('analytics_report', {})
    return bool(report and 'enhanced_dataframe' in report and not report['enhanced_dataframe'].empty)

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

def render_main_content():
    """Render the unified main content - option chain table on top, analytics below."""

    if not is_data_available():
        return

    # Get data
    report = st.session_state.get('analytics_report', {})
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