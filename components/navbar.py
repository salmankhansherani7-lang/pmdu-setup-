"""
Top Header / Navbar — fully dynamic, only shows values extracted from real data.
Never shows hardcoded region, date, or record count.
"""
import streamlit as st
from typing import Optional

def render_top_navbar(
    source_file: str = "",
    region: Optional[str] = None,
    as_of_date: Optional[str] = None,
    total_records: Optional[int] = None,
    is_verified: bool = False,
    validation_status: str = ""
):
    """
    Renders the application header.
    Only displays metadata fields that come from the actual uploaded data.
    """
    meta_parts = []
    if source_file:
        meta_parts.append(f"📁 Source: <b>{source_file}</b>")
    if region and region != "Unknown Region":
        meta_parts.append(f"📍 Region: <b>{region}</b>")
    if as_of_date and as_of_date != "Unknown Date":
        meta_parts.append(f"📅 Reporting Date: <b>{as_of_date}</b>")
    if total_records is not None:
        meta_parts.append(f"📋 Records: <b>{total_records:,}</b>")

    meta_html = " &nbsp;|&nbsp; ".join(meta_parts) if meta_parts else \
        '<span style="color:#94A3B8; font-style:italic;">No file loaded</span>'

    if is_verified:
        badge = '<span class="app-badge-green">✓ Validation Passed</span>'
    elif validation_status:
        badge = f'<span class="app-badge" style="background:#FEF3C7;border-color:#FDE68A;color:#B45309;">⚠ {validation_status.replace("_", " ")}</span>'
    else:
        badge = ""

    st.markdown(f"""
    <div class="app-header-card">
        <div>
            <div class="app-title">PMDU Complaints Analytics</div>
            <div class="app-subtitle">{meta_html}</div>
        </div>
        <div>{badge}</div>
    </div>
    """, unsafe_allow_html=True)


def render_empty_header():
    """Header shown when no file is uploaded."""
    st.markdown("""
    <div class="app-header-card">
        <div>
            <div class="app-title">PMDU Complaints Analytics</div>
            <div class="app-subtitle" style="color:#94A3B8; font-style:italic;">
                Upload an Excel or CSV file using the sidebar to begin analysis.
            </div>
        </div>
        <div>
            <span class="app-badge" style="background:#F1F5F9; border-color:#CBD5E1; color:#64748B;">
                No File Loaded
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
