"""
View: Forwarded Complaints — Citizen grievances routed to departments for inquiry.
"""
import streamlit as st
import pandas as pd
from components.empty_state import empty_chart_placeholder
from components.kpi_cards import render_kpi_card, render_kpi_grid, render_empty_kpi_grid
from components.charts import create_bar_chart

def render_forwarded_page(data_bundle: dict):
    st.markdown("## 📨 Forwarded Complaints")
    st.caption("Citizen grievances routed to respective line departments for administrative action.")

    if not data_bundle.get("has_data"):
        render_empty_kpi_grid([
            "Total Forwarded",
            "Target Departments",
            "Affected Districts"
        ])
        col1, col2 = st.columns(2)
        with col1:
            empty_chart_placeholder("Forwarded by Department")
        with col2:
            empty_chart_placeholder("Forwarded by District")
        return

    format_type = data_bundle.get("format_type")

    if format_type == "pmdu_sectional":
        metrics   = data_bundle.get("sectional_metrics", {})
        sec_data  = metrics.get("sections", {}).get("Forwarded Complaints", {})
        calc_tot  = sec_data.get("calculated_total")
        src_tot   = sec_data.get("source_total")
        formula   = sec_data.get("formula")
        verified  = sec_data.get("is_verified", False)

        cards = [
            render_kpi_card("Total Forwarded (Calculated)", calc_tot, "Independent sum of detail rows", formula, "blue"),
            render_kpi_card("Excel Cached Total", src_tot, "Value cached in spreadsheet cell", "Cell N10", "indigo"),
            render_kpi_card("Verification", "VERIFIED ✓" if verified else "Awaiting Data", "Calculated vs cached match", "", "teal" if verified else "amber"),
        ]
        render_kpi_grid(cards)

        row_items = sec_data.get("row_breakdown", [])
        # Filter out empty rows (where total is None or 0)
        valid_rows = [r for r in row_items if r.get("total") is not None and r["total"] > 0]
        if valid_rows:
            row_dict = {r["label"]: r["total"] for r in valid_rows}
            col1, col2 = st.columns([3, 2])
            with col1:
                st.plotly_chart(create_bar_chart(row_dict, "Forwarded by Subcategory", color="#2563EB"), use_container_width=True)
            with col2:
                st.dataframe(pd.DataFrame([
                    {"Row": r["label"], "Calculated Total": r.get("total"), "Source Total": r.get("source_total"), "Formula": r.get("formula")}
                    for r in valid_rows
                ]), use_container_width=True, hide_index=True)
        else:
            empty_chart_placeholder("Forwarded Complaints by Subcategory")
            st.info("ℹ️ Detail cells are unpopulated in this workbook. Charts will appear once figures are present.")

    else:
        # Standard Tabular Dataset
        df = data_bundle.get("tabular_df")
        mapping = data_bundle.get("mapping", {})
        stat_col = mapping.get("status")
        dept_col = mapping.get("department")
        dist_col = mapping.get("district")

        if not stat_col or stat_col not in df.columns:
            st.info("Map the 'Status' column in Data Quality to isolate Forwarded complaints.")
            return

        # Filter strictly for Forwarded complaints
        fwd_df = df[df[stat_col].astype(str).str.lower().str.contains("forward", na=False)].dropna(how="all")
        total_fwd = len(fwd_df)

        dept_count = fwd_df[dept_col].nunique() if dept_col and dept_col in fwd_df.columns else "N/A"
        dist_count = fwd_df[dist_col].nunique() if dist_col and dist_col in fwd_df.columns else "N/A"

        cards = [
            render_kpi_card("Forwarded Complaints", total_fwd, "Total routed cases", f"{stat_col} = Forwarded", "blue"),
            render_kpi_card("Target Departments", dept_count, "Departments receiving complaints", dept_col or "", "indigo"),
            render_kpi_card("Affected Districts", dist_count, "Districts with forwarded cases", dist_col or "", "teal"),
        ]
        render_kpi_grid(cards)

        # ── Two Relevant Bar Charts for Forwarded Section ──
        col1, col2 = st.columns(2)
        with col1:
            if dept_col and dept_col in fwd_df.columns and total_fwd > 0:
                dept_data = fwd_df[dept_col].dropna().value_counts().to_dict()
                st.plotly_chart(create_bar_chart(dept_data, "Forwarded Complaints by Department", horizontal=True, color="#2563EB"), use_container_width=True)
            else:
                empty_chart_placeholder("Forwarded by Department")

        with col2:
            if dist_col and dist_col in fwd_df.columns and total_fwd > 0:
                dist_data = fwd_df[dist_col].dropna().value_counts().to_dict()
                st.plotly_chart(create_bar_chart(dist_data, "Forwarded Complaints by District", color="#0D9488"), use_container_width=True)
            else:
                empty_chart_placeholder("Forwarded by District")

        # ── Filtered Table (Completely Empty Rows Removed) ──
        st.markdown("### 📋 Active Forwarded Complaints Roster")
        display_fwd = fwd_df.dropna(how="all")
        if not display_fwd.empty:
            st.dataframe(display_fwd, use_container_width=True, hide_index=True)
        else:
            st.info("No forwarded complaints found in this dataset.")
