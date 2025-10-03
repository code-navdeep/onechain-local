"""
This file contains the CSS styles for the OneChain application.
"""

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