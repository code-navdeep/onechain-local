"""
This module contains the visualization engine for the OneChain application,
including the ChartDataManager and OptionsVisualization classes.
"""

import pandas as pd
import altair as alt
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

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