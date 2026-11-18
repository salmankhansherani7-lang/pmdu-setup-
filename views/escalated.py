"""
View: Escalated Complaints — Elevated to higher administrative authority due to urgency or SLA lapse.
"""
import streamlit as st
import pandas as pd
from components.kpi_cards import render_kpi_card, render_kpi_grid, render_empty_kpi_grid
from components.charts import create_bar_chart
from components.empty_state import empty_chart_placeholder

def render_escalated_page(data_bundle: dict):
    st.markdown("## ⚠️ Escalated Complaints")
    st.caption("Complaints elevated to higher administrative authority due to urgency, complexity, or SLA lapse.")

    if not data_bundle.get("has_data"):
        render_empty_kpi_grid([
            "Total Escalated",
            "Escalated Departments",
            "Affected Districts"
        ])
        col1, col2 = st.columns(2)
        with col1:
            empty_chart_placeholder("Escalated Complaints by Department")
        with col2:
            empty_chart_placeholder("Escalated Complaints by District")
        return

    format_type = data_bundle.get("format_type")

    if format_type == "pmdu_sectional":
        metrics = data_bundle.get("sectional_metrics", {})
        sec_data = metrics.get("sections", {}).get("Escalated Complaints", {})
        
        calc_tot = sec_data.get("calculated_total")
        src_tot = sec_data.get("source_total")
        formula = sec_data.get("formula")

        cards = [
            render_kpi_card("Total Escalated", calc_tot, "Calculated sum of detail rows", formula, "amber"),
            render_kpi_card("Excel Cached Total", src_tot, "Reported in template cell", "Cell N19", "indigo"),
            render_kpi_card("Verification State", "VERIFIED" if sec_data.get("is_verified") else "AWAITING DATA", "Mathematical consistency", "Cross-check detail cells", "teal" if sec_data.get("is_verified") else "amber")
        ]
        render_kpi_grid(cards)

        row_items = sec_data.get("row_breakdown", [])
        valid_rows = [r for r in row_items if r.get("total") is not None and r["total"] > 0]
        if valid_rows:
            st.markdown("### 📋 Escalation Breakdown")
            row_dict = {item["label"]: item["total"] for item in valid_rows}
            
            col1, col2 = st.columns([3, 2])
            with col1:
                st.plotly_chart(create_bar_chart(row_dict, "Escalated by Subcategory", color="#F59E0B"), use_container_width=True)
            with col2:
                st.dataframe(pd.DataFrame([
                    {"Subcategory": item["label"], "Calculated Sum": item["total"], "Source Total": item["source_total"]}
                    for item in valid_rows
                ]), use_container_width=True, hide_index=True)
        else:
            empty_chart_placeholder("Escalated Complaints by Subcategory")
            st.info("ℹ️ Detail cells are unpopulated in this workbook. Figures will appear once numbers are present.")

    elif format_type == "standard_tabular":
        df = data_bundle.get("tabular_df")
        mapping = data_bundle.get("mapping", {})
        stat_col = mapping.get("status")
        dept_col = mapping.get("department")
        dist_col = mapping.get("district")

        if not stat_col or stat_col not in df.columns:
            st.info("Tabular dataset does not have a mapped 'Status' column to isolate Escalated complaints.")
            return

        # Filter strictly for Escalated complaints
        esc_df = df[df[stat_col].astype(str).str.lower().str.contains("escalat", na=False)].dropna(how="all")
        total_esc = len(esc_df)

        dept_count = esc_df[dept_col].nunique() if dept_col and dept_col in esc_df.columns else "N/A"
        dist_count = esc_df[dist_col].nunique() if dist_col and dist_col in esc_df.columns else "N/A"

        cards = [
            render_kpi_card("Total Escalated", total_esc, "High-priority / SLA overdue", f"{stat_col} = Escalated", "amber"),
            render_kpi_card("Escalated Departments", dept_count, "Departments with escalations", dept_col or "", "indigo"),
            render_kpi_card("Affected Districts", dist_count, "Districts with escalations", dist_col or "", "teal"),
        ]
        render_kpi_grid(cards)

        # ── Two Relevant Bar Charts for Escalated Section ──
        col1, col2 = st.columns(2)
        with col1:
            if dept_col and dept_col in esc_df.columns and total_esc > 0:
                dept_data = esc_df[dept_col].dropna().value_counts().to_dict()
                st.plotly_chart(create_bar_chart(dept_data, "Escalations by Department", horizontal=True, color="#F59E0B"), use_container_width=True)
            else:
                empty_chart_placeholder("Escalated by Department")

        with col2:
            if dist_col and dist_col in esc_df.columns and total_esc > 0:
                dist_data = esc_df[dist_col].dropna().value_counts().to_dict()
                st.plotly_chart(create_bar_chart(dist_data, "Escalations by District", color="#D97706"), use_container_width=True)
            else:
                empty_chart_placeholder("Escalated by District")

        # ── Detail Table (No Empty Rows) ──
        st.markdown("### 📋 Escalated Complaints Detail")
        display_esc = esc_df.dropna(how="all")
        if not display_esc.empty:
            st.dataframe(display_esc, use_container_width=True, hide_index=True)
        else:
            st.info("No escalated complaints recorded in this dataset.")
