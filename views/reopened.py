"""
View: Reopened Complaints & Citizen Dissatisfaction Analysis.
Tracks complaints re-activated following citizen feedback or quality review.
"""
import streamlit as st
import pandas as pd
from components.kpi_cards import render_kpi_card, render_kpi_grid, render_empty_kpi_grid
from components.charts import create_bar_chart
from components.empty_state import empty_chart_placeholder

def render_reopened_page(data_bundle: dict):
    st.markdown("## 🔄 Reopened Complaints & Review")
    st.caption("Citizen grievances eligible for or subject to second-tier review upon feedback or procedural audit.")

    if not data_bundle.get("has_data"):
        render_empty_kpi_grid([
            "Reopened / Review Cases",
            "Dissatisfied Citizens",
            "Departments Under Review"
        ])
        col1, col2 = st.columns(2)
        with col1:
            empty_chart_placeholder("Review Cases by Department")
        with col2:
            empty_chart_placeholder("Feedback by District")
        return

    format_type = data_bundle.get("format_type")

    st.info("ℹ️ **Integrity Note:** Reopened complaints reflect citizen review opportunities and must not be interpreted as an absolute indicator of departmental inefficiency without examining case complexity.")

    if format_type == "pmdu_sectional":
        metrics = data_bundle.get("sectional_metrics", {})
        sec_data = metrics.get("sections", {}).get("Reopened Complaints", {})
        
        calc_tot = sec_data.get("calculated_total")
        src_tot = sec_data.get("source_total")
        formula = sec_data.get("formula")

        cards = [
            render_kpi_card("Total Reopened", calc_tot, "Calculated sum of detail rows", formula, "purple"),
            render_kpi_card("Excel Cached Total", src_tot, "Reported in template cell", "Cell N28", "indigo"),
            render_kpi_card("Verification State", "VERIFIED" if sec_data.get("is_verified") else "AWAITING DATA", "Mathematical consistency", "Cross-check detail cells", "teal" if sec_data.get("is_verified") else "amber")
        ]
        render_kpi_grid(cards)

        row_items = sec_data.get("row_breakdown", [])
        valid_rows = [r for r in row_items if r.get("total") is not None and r["total"] > 0]
        if valid_rows:
            st.markdown("### 📋 Reopening Grounds / Subcategories")
            row_dict = {item["label"]: item["total"] for item in valid_rows}
            
            col1, col2 = st.columns([3, 2])
            with col1:
                st.plotly_chart(create_bar_chart(row_dict, "Reopened Complaints by Reason", color="#8B5CF6"), use_container_width=True)
            with col2:
                st.dataframe(pd.DataFrame([
                    {"Grounds": item["label"], "Calculated Sum": item["total"], "Source Total": item["source_total"]}
                    for item in valid_rows
                ]), use_container_width=True, hide_index=True)
        else:
            empty_chart_placeholder("Reopened Complaints by Grounds")
            st.info("ℹ️ Detail cells are unpopulated in this workbook. Figures will appear once numbers are present.")

    elif format_type == "standard_tabular":
        df = data_bundle.get("tabular_df")
        mapping = data_bundle.get("mapping", {})
        stat_col = mapping.get("status")
        dept_col = mapping.get("department")
        dist_col = mapping.get("district")

        # Check for direct 'reopen' status
        reopen_df = pd.DataFrame()
        if stat_col and stat_col in df.columns:
            reopen_df = df[df[stat_col].astype(str).str.lower().str.contains("reopen", na=False)]

        # Check for Dissatisfied citizen feedback (grounds for reopening under PMDU SOP)
        feedback_col = None
        for col in ["Citizen_Feedback", "feedback", "Feedback", "Satisfaction"]:
            if col in df.columns:
                feedback_col = col
                break

        dissatisfied_df = pd.DataFrame()
        if feedback_col:
            dissatisfied_df = df[df[feedback_col].astype(str).str.lower().str.contains("dissatisfied", na=False)]

        target_df = reopen_df if not reopen_df.empty else dissatisfied_df
        target_label = "Reopened Status" if not reopen_df.empty else "Dissatisfied Feedback (Reopen Grounds)"

        cards = [
            render_kpi_card("Review Candidates", len(target_df), target_label, feedback_col or stat_col or "", "purple"),
            render_kpi_card("Departments Affected", target_df[dept_col].nunique() if dept_col and dept_col in target_df.columns else "N/A", "Departments receiving feedback", dept_col or "", "indigo"),
            render_kpi_card("Affected Districts", target_df[dist_col].nunique() if dist_col and dist_col in target_df.columns else "N/A", "Districts requesting review", dist_col or "", "teal"),
        ]
        render_kpi_grid(cards)

        # ── Two Relevant Bar Charts for Reopened Section ──
        col1, col2 = st.columns(2)
        with col1:
            if dept_col and dept_col in target_df.columns and len(target_df) > 0:
                dept_data = target_df[dept_col].dropna().value_counts().to_dict()
                st.plotly_chart(create_bar_chart(dept_data, "Review Candidates by Department", horizontal=True, color="#8B5CF6"), use_container_width=True)
            else:
                empty_chart_placeholder("Review Cases by Department")

        with col2:
            if dist_col and dist_col in target_df.columns and len(target_df) > 0:
                dist_data = target_df[dist_col].dropna().value_counts().to_dict()
                st.plotly_chart(create_bar_chart(dist_data, "Citizen Dissatisfaction by District", color="#7C3AED"), use_container_width=True)
            else:
                empty_chart_placeholder("Feedback by District")

        # ── Detail Table (Completely Empty Rows Removed) ──
        st.markdown("### 📋 Cases Subject to Review / Reopening Grounds")
        clean_target = target_df.dropna(how="all")
        if not clean_target.empty:
            st.dataframe(clean_target, use_container_width=True, hide_index=True)
        else:
            st.info("No cases identified with reopened status or dissatisfied feedback.")
