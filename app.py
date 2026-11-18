"""
PMDU Complaints Analytics & Monitoring Platform
Main Orchestrator — Fully Dynamic, Zero Hardcoded Data.
Starts in an empty state; all analytics driven by the active file.
"""
import streamlit as st
import os
import io

from config import APP_TITLE, BASE_DIR, MAX_UPLOAD_SIZE_MB, ALLOWED_EXTENSIONS
from core.format_detector import detect_file_format
from core.excel_reader import get_excel_sheets, read_excel_tabular
from core.csv_reader import read_csv_safe
from core.sectional_parser import parse_pmdu_sectional_workbook, sectional_to_flat_dataframe
from core.column_mapping import auto_suggest_mappings
from core.validation import validate_sectional_dataset, validate_tabular_dataset
from core.calculations import calculate_sectional_metrics, calculate_tabular_metrics
from components.navbar import render_top_navbar, render_empty_header
from components.sidebar import render_sidebar

# Page Renderers
from views.overview import render_overview_page
from views.forwarded import render_forwarded_page
from views.escalated import render_escalated_page
from views.reopened import render_reopened_page
from views.response_awaited import render_response_awaited_page
from views.data_quality import render_data_quality_page
from views.data_table import render_data_table_page
from views.geographical import render_geographical_page
from views.trends import render_trends_page
from views.reports import render_reports_page

# ── Page Configuration ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="PMDU Complaints Analytics",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject Modern Enterprise CSS ─────────────────────────────────────────────
css_file = os.path.join(BASE_DIR, "styles", "custom.css")
if os.path.exists(css_file):
    with open(css_file, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Auto-Load Local input_data.xlsx on first launch if present ────────────────
from config import DEFAULT_INPUT_FILE
if "raw_uploaded_file" not in st.session_state and not st.session_state.get("_user_cleared"):
    if os.path.exists(DEFAULT_INPUT_FILE):
        with open(DEFAULT_INPUT_FILE, "rb") as f:
            file_bytes = f.read()
        st.session_state["raw_uploaded_file"] = file_bytes
        st.session_state["current_uploaded_filename"] = "input_data.xlsx"
        st.session_state["dataset_source_label"] = "input_data.xlsx"
        st.session_state["_file_key"] = f"input_data.xlsx_{len(file_bytes)}"

# ── Render Sidebar (Navigation + Dynamic Upload) ─────────────────────────────
render_sidebar()

# ── Retrieve File State ──────────────────────────────────────────────────────
raw_file = st.session_state.get("raw_uploaded_file")
filename = st.session_state.get("current_uploaded_filename", "")
ds_label = st.session_state.get("dataset_source_label", "")
active_page = st.session_state.get("active_page", "Overview")

PAGE_MAP = {
    "Overview": render_overview_page,
    "Forwarded Complaints": render_forwarded_page,
    "Escalated Complaints": render_escalated_page,
    "Reopened Complaints": render_reopened_page,
    "Response Awaited": render_response_awaited_page,
    "Data Quality": render_data_quality_page,
    "Data Table": render_data_table_page,
    "Geographic Analysis": render_geographical_page,
    "Trends": render_trends_page,
    "Reports": render_reports_page,
}

# ── Handle Empty State (No File Loaded) ──────────────────────────────────────
if raw_file is None:
    render_empty_header()
    from config import DEFAULT_INPUT_FILE
    if os.path.exists(DEFAULT_INPUT_FILE):
        col_info, col_btn = st.columns([3, 1])
        with col_info:
            st.info("💡 **Local data file found:** `input_data.xlsx` is present in your folder. Click the button to load it, or upload any file in the sidebar.")
        with col_btn:
            if st.button("🚀 Load input_data.xlsx", type="primary", use_container_width=True, key="btn_load_local_main"):
                with open(DEFAULT_INPUT_FILE, "rb") as f:
                    file_bytes = f.read()
                st.session_state["raw_uploaded_file"] = file_bytes
                st.session_state["current_uploaded_filename"] = "input_data.xlsx"
                st.session_state["dataset_source_label"] = "input_data.xlsx"
                st.session_state["_file_key"] = f"input_data.xlsx_{len(file_bytes)}"
                st.rerun()

    empty_bundle = {
        "format_type": None,
        "filename": "",
        "dataset_name": "",
        "has_data": False,
    }
    render_fn = PAGE_MAP.get(active_page, render_overview_page)
    render_fn(empty_bundle)
    st.stop()

# ── Convert Raw Bytes to BytesIO ────────────────────────────────────────────
if isinstance(raw_file, bytes):
    file_bytes_io = io.BytesIO(raw_file)
elif hasattr(raw_file, "read"):
    file_bytes_io = io.BytesIO(raw_file.read())
else:
    file_bytes_io = raw_file

# ── Write temporary working copy for format detection ───────────────────────
safe_name = os.path.basename(filename).replace(" ", "_")
temp_path = os.path.join(BASE_DIR, "data", "uploads", f"temp_{safe_name}")
os.makedirs(os.path.dirname(temp_path), exist_ok=True)
with open(temp_path, "wb") as f:
    f.write(file_bytes_io.getvalue())

# ── File Type & Size Validation ─────────────────────────────────────────────
ext = os.path.splitext(filename)[1].lower()
if ext not in ALLOWED_EXTENSIONS:
    render_empty_header()
    st.error(f"**Unsupported file format:** `{ext}`. Please upload an Excel (.xlsx, .xls) or CSV file.")
    st.stop()

file_size_mb = len(file_bytes_io.getvalue()) / (1024 * 1024)
if file_size_mb > MAX_UPLOAD_SIZE_MB:
    render_empty_header()
    st.error(f"**File size exceeds limit:** {file_size_mb:.1f} MB (maximum allowed: {MAX_UPLOAD_SIZE_MB} MB).")
    st.stop()

# ── Detect Format ────────────────────────────────────────────────────────────
detected = detect_file_format(temp_path)
format_type = detected.get("format", "standard_tabular")
all_sheets = detected.get("sheets", [])

# Multi-sheet selection in sidebar if applicable
sheet_name = None
if format_type in ["pmdu_sectional", "standard_tabular"] and ext in [".xlsx", ".xls"]:
    if len(all_sheets) > 1:
        sheet_name = st.sidebar.selectbox("📄 Select Worksheet", all_sheets, key="worksheet_selector")
    elif len(all_sheets) == 1:
        sheet_name = all_sheets[0]

# ── Process Data Bundle ─────────────────────────────────────────────────────
data_bundle = {
    "format_type": format_type,
    "filename": filename,
    "dataset_name": ds_label or filename,
    "sheet_name": sheet_name,
    "has_data": False,
}

try:
    if format_type == "pmdu_sectional":
        # PMDU 4-Section Matrix
        cfg_cols = st.session_state.get("configured_sectional_cols")
        cfg_rows = st.session_state.get("configured_sectional_rows")

        file_bytes_io.seek(0)
        parsed_sec = parse_pmdu_sectional_workbook(
            file_bytes_io,
            sheet_name=sheet_name,
            column_labels=cfg_cols,
            row_labels_map=cfg_rows
        )

        if not parsed_sec.get("success"):
            render_empty_header()
            st.error(f"**Could not parse sectional workbook:** {parsed_sec.get('error', 'Unknown parsing error.')}")
            st.stop()

        val_report  = validate_sectional_dataset(parsed_sec)
        sec_metrics = calculate_sectional_metrics(parsed_sec)
        flat_df     = sectional_to_flat_dataframe(parsed_sec)

        data_bundle.update({
            "parsed_sectional": parsed_sec,
            "sectional_metrics": sec_metrics,
            "validation_report": val_report,
            "flat_df": flat_df,
            "is_populated": parsed_sec.get("is_populated", False),
            "has_data": True,
        })

        # Dynamic Header (only authentic metadata)
        region = parsed_sec.get("region")
        as_date = parsed_sec.get("as_of_date")
        
        render_top_navbar(
            source_file=filename,
            region=region if region != "Unknown Region" else None,
            as_of_date=as_date if as_date != "Unknown Date" else None,
            total_records=None,
            is_verified=(val_report.get("status") in ["PASSED", "PASSED_WITH_WARNINGS"]),
            validation_status=val_report.get("status", "")
        )

    else:
        # Standard Tabular (CSV or Tabular Excel)
        file_bytes_io.seek(0)
        if ext == ".csv":
            read_res = read_csv_safe(file_bytes_io)
        else:
            read_res = read_excel_tabular(file_bytes_io, sheet_name=sheet_name)

        if not read_res.get("success"):
            render_empty_header()
            st.error(f"**Could not read file:** {read_res.get('error', 'Unknown error.')}")
            st.stop()

        df_raw = read_res.get("dataframe")
        if df_raw is None or df_raw.empty:
            render_empty_header()
            st.warning("**The uploaded file contains no data rows.** Please upload a populated file.")
            st.stop()

        suggested = auto_suggest_mappings(list(df_raw.columns))
        if "user_column_mapping" not in st.session_state:
            st.session_state["user_column_mapping"] = suggested
        active_mapping = st.session_state["user_column_mapping"]

        val_report  = validate_tabular_dataset(df_raw, active_mapping)
        tab_metrics = calculate_tabular_metrics(df_raw, active_mapping)

        data_bundle.update({
            "tabular_df": df_raw,
            "mapping": active_mapping,
            "validation_report": val_report,
            "tabular_metrics": tab_metrics,
            "has_data": True,
        })

        # Dynamic Header
        region_col = active_mapping.get("region")
        region_val = None
        if region_col and region_col in df_raw.columns:
            unique_regions = df_raw[region_col].dropna().unique()
            if len(unique_regions) == 1:
                region_val = str(unique_regions[0])
            elif len(unique_regions) > 1:
                region_val = f"{len(unique_regions)} regions"

        date_col = active_mapping.get("submission_date")
        date_range = None
        if date_col and date_col in df_raw.columns:
            parsed_dates = df_raw[date_col].dropna()
            if len(parsed_dates):
                date_range = f"{parsed_dates.min()} → {parsed_dates.max()}"

        render_top_navbar(
            source_file=filename,
            region=region_val,
            as_of_date=date_range,
            total_records=len(df_raw),
            is_verified=(val_report.get("status") in ["PASSED", "PASSED_WITH_WARNINGS"]),
            validation_status=val_report.get("status", "")
        )

except Exception as e:
    render_empty_header()
    st.error(f"**Unexpected error while processing file:** {str(e)}")
    import traceback
    with st.expander("Technical Error Details"):
        st.code(traceback.format_exc())
    st.stop()

# ── Page Router ─────────────────────────────────────────────────────────────
render_fn = PAGE_MAP.get(active_page, render_overview_page)
render_fn(data_bundle)
