"""
Configurator UI Components:
1. Sectional Matrix Label Configurator: allows naming unpopulated columns C-M & detail rows.
2. Tabular Column Mapper: maps CSV/Excel columns to standard complaint schema.
"""
import streamlit as st
from typing import Dict, Any, List
from config import STANDARD_FIELDS
from core.column_mapping import auto_suggest_mappings

def render_sectional_label_configurator(parsed_sectional: Dict[str, Any]):
    """
    Renders an interactive configurator for unpopulated sectional matrix headers.
    """
    st.markdown("""
    <div class="content-card">
        <div class="content-card-title">
            <span>⚙️ Sectional Matrix Header & Row Label Configurator</span>
            <span class="status-pill status-warning">Manual Configuration Mode</span>
        </div>
        <p style="font-size: 13px; color: #64748B;">
            The uploaded PMDU matrix report has unpopulated column and detail row headers.
            In strict compliance with <b>Zero-Tolerance Rules</b>, the platform does not invent these labels.
            You can configure meaningful entities (e.g. Districts, Tehsils, or Offices) below:
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📝 Configure Column Entities (Columns C through M)", expanded=False):
        st.caption("11 detail columns detected in report layout:")
        current_cols = parsed_sectional.get("column_labels", [f"Entity_{chr(65+i)}" for i in range(2, 13)])
        
        cols_ui = st.columns(3)
        new_cols = []
        for i, default_val in enumerate(current_cols):
            with cols_ui[i % 3]:
                val = st.text_input(f"Column {chr(67+i)} Entity", value=default_val, key=f"sec_col_cfg_{i}")
                new_cols.append(val.strip() if val.strip() else default_val)
        
        if st.button("Apply Column Labels", key="btn_apply_cols"):
            st.session_state["configured_sectional_cols"] = new_cols
            st.success("Column entity labels updated.")
            st.rerun()

    with st.expander("📋 Configure Detail Row Categories per Section", expanded=False):
        sections = parsed_sectional.get("sections", {})
        new_row_maps = {}
        for sec_name, s_data in sections.items():
            st.markdown(f"**{sec_name}** ({s_data['detail_rows_count']} rows):")
            r_cols = st.columns(2)
            sec_row_labels = []
            for r_i, rec in enumerate(s_data.get("detail_records", [])):
                with r_cols[r_i % 2]:
                    r_val = st.text_input(
                        f"Row {r_i+1} Label",
                        value=rec["row_label"],
                        key=f"sec_row_cfg_{sec_name}_{r_i}"
                    )
                    sec_row_labels.append(r_val.strip() if r_val.strip() else rec["row_label"])
            new_row_maps[sec_name] = sec_row_labels
        
        if st.button("Apply Row Labels", key="btn_apply_rows"):
            st.session_state["configured_sectional_rows"] = new_row_maps
            st.success("Row category labels updated.")
            st.rerun()


def render_tabular_column_mapper(df_columns: List[str]) -> Dict[str, str]:
    """
    Renders the interactive column mapping interface for standard tabular data.
    """
    st.markdown("""
    <div class="content-card">
        <div class="content-card-title">
            <span>🗺️ Column Mapping Interface</span>
            <span class="status-pill status-passed">Auto-Mapping Active</span>
        </div>
        <p style="font-size: 13px; color: #64748B;">
            Map columns from your dataset to standard analytical dimensions.
            Only dimensions with mapped columns will be activated across the dashboard.
        </p>
    </div>
    """, unsafe_allow_html=True)

    suggestions = auto_suggest_mappings(df_columns)
    user_mapping = {}

    options = ["-- Unmapped / Not Present --"] + df_columns

    with st.expander("🛠️ Review & Adjust Column Mappings", expanded=True):
        col_ui_1, col_ui_2 = st.columns(2)
        items = list(STANDARD_FIELDS.items())
        half = (len(items) + 1) // 2

        for idx, (field_key, field_meta) in enumerate(items):
            target_col_ui = col_ui_1 if idx < half else col_ui_2
            with target_col_ui:
                suggested_col = suggestions.get(field_key)
                default_idx = (options.index(suggested_col)) if (suggested_col in options) else 0
                
                selected = st.selectbox(
                    f"{field_meta['label']}",
                    options=options,
                    index=default_idx,
                    key=f"col_map_sel_{field_key}",
                    help=f"Standard type: {field_meta['type']}"
                )
                if selected != "-- Unmapped / Not Present --":
                    user_mapping[field_key] = selected
                else:
                    user_mapping[field_key] = None

    return user_mapping

