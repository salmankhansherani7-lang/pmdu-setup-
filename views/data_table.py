"""
View: Data Table — Master Data Explorer with interactive filtering, column selection, and CSV export.
Removes all completely empty rows and displays real-time filtered bar chart.
"""
import streamlit as st
import pandas as pd
from components.empty_state import no_data_placeholder
from components.charts import create_bar_chart

def render_data_table_page(data_bundle: dict):
    st.markdown("## 🔍 Data Table")
    st.caption("Inspect, filter, search, and export granular complaint records with complete fidelity.")

    if not data_bundle.get("has_data"):
        no_data_placeholder("🔍", "No Data Available", "Upload an Excel or CSV file in the sidebar to view and filter records.")
        return

    format_type = data_bundle.get("format_type")

    if format_type == "pmdu_sectional":
        df = data_bundle.get("flat_df")
        st.info("ℹ️ **Tabular View of PMDU Matrix:** Normalized view of all populated detail cells across sections.")
    else:
        df = data_bundle.get("tabular_df")

    if df is None or df.empty:
        st.warning("No data available to display in table.")
        return

    # ── Remove Completely Empty Rows ──
    df_clean = df.dropna(how="all").copy()

    # Search & Quick Filters
    col_search, col_sec, col_dist = st.columns([2, 1, 1])
    with col_search:
        search_query = st.text_input("🔎 Search text in any column", placeholder="Type keywords...")
    
    filtered_df = df_clean.copy()

    # Dynamic Filter 1: Status or Section
    if "Status" in filtered_df.columns:
        with col_sec:
            stat_options = ["All Statuses"] + sorted(list(filtered_df["Status"].dropna().unique()))
            sel_stat = st.selectbox("Filter Status", stat_options)
            if sel_stat != "All Statuses":
                filtered_df = filtered_df[filtered_df["Status"] == sel_stat]
    elif "Section" in filtered_df.columns:
        with col_sec:
            sec_options = ["All Sections"] + sorted(list(filtered_df["Section"].dropna().unique()))
            sel_sec = st.selectbox("Filter Section", sec_options)
            if sel_sec != "All Sections":
                filtered_df = filtered_df[filtered_df["Section"] == sel_sec]

    # Dynamic Filter 2: District or Department
    if "District" in filtered_df.columns:
        with col_dist:
            dist_options = ["All Districts"] + sorted(list(filtered_df["District"].dropna().unique()))
            sel_dist = st.selectbox("Filter District", dist_options)
            if sel_dist != "All Districts":
                filtered_df = filtered_df[filtered_df["District"] == sel_dist]
    elif "Department" in filtered_df.columns:
        with col_dist:
            dept_options = ["All Departments"] + sorted(list(filtered_df["Department"].dropna().unique()))
            sel_dept = st.selectbox("Filter Department", dept_options)
            if sel_dept != "All Departments":
                filtered_df = filtered_df[filtered_df["Department"] == sel_dept]

    # Global text search
    if search_query.strip():
        mask = filtered_df.astype(str).apply(lambda row: row.str.contains(search_query.strip(), case=False).any(), axis=1)
        filtered_df = filtered_df[mask]

    # Remove completely empty rows from filtered view
    filtered_df = filtered_df.dropna(how="all")

    # ── Relevant Bar Chart for Filtered Data View ──
    if not filtered_df.empty:
        col_chart_target = "Department" if "Department" in filtered_df.columns else ("District" if "District" in filtered_df.columns else None)
        if col_chart_target:
            chart_data = filtered_df[col_chart_target].dropna().value_counts().head(8).to_dict()
            st.plotly_chart(create_bar_chart(chart_data, f"Filtered Records by {col_chart_target} ({len(filtered_df):,} records)", color="#2563EB"), use_container_width=True)

    # Column Selection
    all_cols = list(filtered_df.columns)
    with st.expander("👁️ Select Visible Columns", expanded=False):
        selected_cols = st.multiselect("Columns to display", options=all_cols, default=all_cols[:10])
        if not selected_cols:
            selected_cols = all_cols

    display_df = filtered_df[selected_cols].dropna(how="all")

    # Summary bar
    st.markdown(f"**Showing {len(display_df):,} valid records (out of {len(df_clean):,} total)**")

    # Dataframe with sorting and scrolling
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    # Export CSV button
    csv_bytes = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Filtered Records (CSV)",
        data=csv_bytes,
        file_name="pmdu_complaints_filtered.csv",
        mime="text/csv",
        help="Download filtered records as CSV"
    )
