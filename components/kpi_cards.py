"""
KPI Card component:
Displays metrics with full audit traceability tags, variance, and verification state.
Supports empty state with '—' when value is None.
"""
import streamlit as st
from typing import Optional, Any

def render_kpi_card(
    label: str,
    value: Any,
    subtext: str = "",
    trace_tag: Optional[str] = None,
    card_type: str = "blue"
) -> str:
    """
    card_type can be: 'blue', 'teal', 'amber', 'indigo', 'purple'
    """
    if value is None:
        val_display = '<span style="color:#94A3B8; font-size:22px; font-weight:700;">—</span>'
    else:
        val_display = str(value)

    tag_html = f'<div class="kpi-trace-tag">SRC: {trace_tag}</div>' if trace_tag else ''
    
    html = f"""
    <div class="kpi-card kpi-card-{card_type}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{val_display}</div>
        <div class="kpi-subtext">{subtext}</div>
        {tag_html}
    </div>
    """
    return html

def render_kpi_grid(cards_html_list):
    cards_str = "\n".join(cards_html_list)
    html = f"""
    <div class="kpi-container">
        {cards_str}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_empty_kpi_grid(labels: list):
    """Show placeholder KPI cards before data is loaded."""
    cards = [render_kpi_card(lbl, None, "No data available", None, "blue") for lbl in labels]
    render_kpi_grid(cards)
