"""
View: Overview — High-level summary of complaints performance and workflow breakdown.
"""
import streamlit as st
import pandas as pd
from components.kpi_cards import render_kpi_card, render_kpi_grid, render_empty_kpi_grid
from components.charts import create_bar_chart, create_donut_chart
from components.empty_state import empty_chart_placeholder

def render_overview_page(data_bundle: dict):
    st.markdown("## 📊 Overview")
    st.caption("Operational intelligence and workflow performance summary.")

    if not data_bundle.get("has_data"):
        render_empty_kpi_grid([
            "Total Complaints",
            "Resolved Complaints",
            "Resolution Rate",
            "Pending / In-Progress"
        ])
        col1, col2 = st.columns(2)
        with col1:
            empty_chart_placeholder("Complaints by Workflow Status")
        with col2:
            empty_chart_placeholder("Complaints by Department")
        return

    format_type = data_bundle.get("format_type")

    if format_type == "pmdu_sectional":
        metrics  = data_bundle.get("sectional_metrics", {})
        sections = metrics.get("sections", {})

        f_info = sections.get("Forwarded Complaints", {})
        e_info = sections.get("Escalated Complaints", {})
        r_info = sections.get("Reopened Complaints", {})
        a_info = sections.get("Response Awaited Complaints", {})

        cards = [
            render_kpi_card("Forwarded Complaints",     f_info.get("calculated_total"), "Departmental routing",           f_info.get("formula"), "blue"),
            render_kpi_card("Escalated Complaints",     e_info.get("calculated_total"), "Supervisory escalation",         e_info.get("formula"), "amber"),
            render_kpi_card("Reopened Complaints",      r_info.get("calculated_total"), "Citizen review / re-activation", r_info.get("formula"), "purple"),
            render_kpi_card("Response Awaited",         a_info.get("calculated_total"), "Pending departmental reply",      a_info.get("formula"), "teal"),
        ]
        render_kpi_grid(cards)

        st.info("ℹ️ **Integrity Notice:** Forwarded, Escalated, Reopened, and Response Awaited are distinct workflow stages. They are not combined into one total without verified mutual exclusivity.")

        section_totals = {
            k: v.get("calculated_total")
            for k, v in sections.items()
            if v.get("calculated_total") is not None and v.get("calculated_total") > 0
        }
        if section_totals:
            col1, col2 = st.columns([3, 2])
            with col1:
                st.plotly_chart(create_bar_chart(section_totals, "Operational Volume by Workflow Section", color="#2563EB"), use_container_width=True)
            with col2:
                st.plotly_chart(create_donut_chart(section_totals, "Proportional Share"), use_container_width=True)
        else:
            st.info("ℹ️ Detail cells in this workbook are unpopulated. Charts will populate once numbers are entered.")

    else:
        # Standard Tabular Dataset
        df = data_bundle.get("tabular_df")
        mapping = data_bundle.get("mapping", {})
        t = data_bundle.get("tabular_metrics", {})

        total_cnt = len(df)
        stat_col = mapping.get("status")
        dept_col = mapping.get("department")
        dist_col = mapping.get("district")

        resolved_cnt = 0
        if stat_col and stat_col in df.columns:
            resolved_cnt = len(df[df[stat_col].astype(str).str.lower().str.contains("resolve|closed", na=False)])

        res_rate = round((resolved_cnt / total_cnt * 100), 1) if total_cnt > 0 else 0
        pending_cnt = total_cnt - resolved_cnt

        cards = [
            render_kpi_card("Total Complaints", total_cnt, "Total verified records", "Dataset Row Count", "blue"),
            render_kpi_card("Resolved Complaints", resolved_cnt, "Successfully disposed", f"{stat_col} = Resolved", "teal"),
            render_kpi_card("Resolution Rate", f"{res_rate}%", "Share of resolved cases", "Resolved ÷ Total", "indigo"),
            render_kpi_card("Active / In-Progress", pending_cnt, "Currently in workflow", "Pending disposal", "amber"),
        ]
        render_kpi_grid(cards)

        # ── Two Key Bar Charts ──
        col1, col2 = st.columns(2)
        with col1:
            if stat_col and stat_col in df.columns:
                stat_dist = df[stat_col].dropna().value_counts().to_dict()
                fig_status = create_bar_chart(stat_dist, "Complaints by Workflow Status", y_label="Total Cases", color="#2563EB")
                st.plotly_chart(fig_status, use_container_width=True)
            else:
                st.info("Map Status column in Data Quality to view Status breakdown.")

        with col2:
            if dept_col and dept_col in df.columns:
                dept_dist = df[dept_col].dropna().value_counts().head(8).to_dict()
                fig_dept = create_bar_chart(dept_dist, "Complaints by Department", horizontal=True, color="#0D9488")
                st.plotly_chart(fig_dept, use_container_width=True)
            elif dist_col and dist_col in df.columns:
                dist_dist = df[dist_col].dropna().value_counts().to_dict()
                fig_dist = create_bar_chart(dist_dist, "Complaints by District", color="#0D9488")
                st.plotly_chart(fig_dist, use_container_width=True)

        # ── Summary Breakdown Table (No Empty Rows) ──
        if dept_col and dept_col in df.columns and stat_col and stat_col in df.columns:
            st.markdown("### 🏢 Departmental Performance Summary")
            clean_df = df.dropna(subset=[dept_col, stat_col])
            dept_summary = clean_df.groupby(dept_col).agg(
                Total=(clean_df.columns[0], 'count'),
                Resolved=(stat_col, lambda s: s.astype(str).str.lower().str.contains("resolve|closed").sum()),
                In_Progress=(stat_col, lambda s: (~s.astype(str).str.lower().str.contains("resolve|closed")).sum())
            ).reset_index()
            dept_summary["Resolution_Rate"] = (dept_summary["Resolved"] / dept_summary["Total"] * 100).round(1).astype(str) + "%"
            dept_summary = dept_summary.sort_values(by="Total", ascending=False)
            
            # Remove any empty or 0-count rows
            dept_summary = dept_summary[dept_summary["Total"] > 0]
            st.dataframe(dept_summary, use_container_width=True, hide_index=True)
