"""
View: Response Awaited Complaints — Formal compliance or inquiry reports pending from departments.
"""
import streamlit as st
import pandas as pd
from components.kpi_cards import render_kpi_card, render_kpi_grid, render_empty_kpi_grid
from components.charts import create_bar_chart
from components.empty_state import empty_chart_placeholder

def render_response_awaited_page(data_bundle: dict):
    st.markdown("## ⏳ Response Awaited")
    st.caption("Complaints pending submission of formal compliance or departmental inquiry reports.")

    if not data_bundle.get("has_data"):
        render_empty_kpi_grid([
            "Total Awaited",
            "Departments Awaiting",
            "Districts Pending"
        ])
        col1, col2 = st.columns(2)
        with col1:
            empty_chart_placeholder("Pending Response by Department")
        with col2:
            empty_chart_placeholder("Pending Response by District")
        return

    format_type = data_bundle.get("format_type")

    if format_type == "pmdu_sectional":
        metrics = data_bundle.get("sectional_metrics", {})
        sec_data = metrics.get("sections", {}).get("Response Awaited Complaints", {})
        
        calc_tot = sec_data.get("calculated_total")
        src_tot = sec_data.get("source_total")
        formula = sec_data.get("formula")

        cards = [
            render_kpi_card("Total Awaited", calc_tot, "Calculated sum of detail rows", formula, "teal"),
            render_kpi_card("Excel Cached Total", src_tot, "Reported in template cell", "Cell N35", "indigo"),
            render_kpi_card("Verification State", "VERIFIED" if sec_data.get("is_verified") else "AWAITING DATA", "Mathematical consistency", "Cross-check detail cells", "teal" if sec_data.get("is_verified") else "amber")
        ]
        render_kpi_grid(cards)

        row_items = sec_data.get("row_breakdown", [])
        valid_rows = [r for r in row_items if r.get("total") is not None and r["total"] > 0]
        if valid_rows:
            st.markdown("### 📋 Detail Categories")
            row_dict = {item["label"]: item["total"] for item in valid_rows}
            
            col1, col2 = st.columns([3, 2])
            with col1:
                st.plotly_chart(create_bar_chart(row_dict, "Response Awaited by Category", color="#0F9D91"), use_container_width=True)
            with col2:
                st.dataframe(pd.DataFrame([
                    {"Category": item["label"], "Calculated Sum": item["total"], "Source Total": item["source_total"]}
                    for item in valid_rows
                ]), use_container_width=True, hide_index=True)
        else:
            empty_chart_placeholder("Response Awaited by Category")
            st.info("ℹ️ Detail cells are unpopulated in this workbook. Figures will appear once numbers are present.")

    elif format_type == "standard_tabular":
        df = data_bundle.get("tabular_df")
        mapping = data_bundle.get("mapping", {})
        stat_col = mapping.get("status")
        dept_col = mapping.get("department")
        dist_col = mapping.get("district")

        if not stat_col or stat_col not in df.columns:
            st.info("Tabular dataset does not have a mapped 'Status' column to isolate Response Awaited complaints.")
            return

        # Filter strictly for Response Awaited complaints
        aw_df = df[df[stat_col].astype(str).str.lower().str.contains("await|pending", na=False)].dropna(how="all")
        total_aw = len(aw_df)

        dept_count = aw_df[dept_col].nunique() if dept_col and dept_col in aw_df.columns else "N/A"
        dist_count = aw_df[dist_col].nunique() if dist_col and dist_col in aw_df.columns else "N/A"

        cards = [
            render_kpi_card("Total Awaited", total_aw, "Formal replies pending", f"{stat_col} contains Awaited", "teal"),
            render_kpi_card("Departments Awaiting", dept_count, "Agencies with pending replies", dept_col or "", "indigo"),
            render_kpi_card("Districts Pending", dist_count, "Districts awaiting answers", dist_col or "", "blue"),
        ]
        render_kpi_grid(cards)

        # ── Two Relevant Bar Charts for Response Awaited Section ──
        col1, col2 = st.columns(2)
        with col1:
            if dept_col and dept_col in aw_df.columns and total_aw > 0:
                dept_data = aw_df[dept_col].dropna().value_counts().to_dict()
                st.plotly_chart(create_bar_chart(dept_data, "Pending Responses by Department", horizontal=True, color="#0D9488"), use_container_width=True)
            else:
                empty_chart_placeholder("Pending Response by Department")

        with col2:
            if dist_col and dist_col in aw_df.columns and total_aw > 0:
                dist_data = aw_df[dist_col].dropna().value_counts().to_dict()
                st.plotly_chart(create_bar_chart(dist_data, "Pending Responses by District", color="#059669"), use_container_width=True)
            else:
                empty_chart_placeholder("Pending Response by District")

        # ── Detail Table (No Empty Rows) ──
        st.markdown("### 📋 Response Awaited Complaints Roster")
        display_aw = aw_df.dropna(how="all")
        if not display_aw.empty:
            st.dataframe(display_aw, use_container_width=True, hide_index=True)
        else:
            st.info("No response-awaited complaints recorded in this dataset.")
