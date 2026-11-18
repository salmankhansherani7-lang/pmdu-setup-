"""
View: Geographic Analysis — Spatial and administrative distribution across Districts and Regions.
Strictly relies on verified columns in the dataset. Never invents geographic entities.
"""
import streamlit as st
import pandas as pd
from components.charts import create_bar_chart, create_donut_chart, create_grouped_bar_chart
from components.empty_state import no_data_placeholder, empty_chart_placeholder
from components.kpi_cards import render_kpi_card, render_kpi_grid

def render_geographical_page(data_bundle: dict):
    st.markdown("## 🗺️ Geographic Analysis")
    st.caption("Administrative distribution and resolution performance across verified territories.")

    if not data_bundle.get("has_data"):
        no_data_placeholder("🗺️", "No Geographic Data Available", "Upload an Excel or CSV file in the sidebar to view regional distribution.")
        return

    format_type = data_bundle.get("format_type")

    if format_type == "pmdu_sectional":
        region = data_bundle.get("parsed_sectional", {}).get("region")
        col_labels = data_bundle.get("parsed_sectional", {}).get("column_labels", [])
        
        if region:
            st.markdown(f"**Identified Operational Region:** `{region}`")
        st.info("ℹ️ **Integrity Rule:** In the PMDU Sectional Report template, Columns C through M represent operational entities. If configured, their distribution is displayed below:")

        metrics = data_bundle.get("sectional_metrics", {})
        sections = metrics.get("sections", {})
        
        entity_totals = {c: 0 for c in col_labels}
        has_data = False
        for s_name, s_data in sections.items():
            for item in s_data.get("col_breakdown", []):
                ent = item["entity"]
                cnt = item["total"]
                if cnt is not None and cnt > 0:
                    entity_totals[ent] += cnt
                    has_data = True

        if has_data and any(v > 0 for v in entity_totals.values()):
            filtered_entities = {k: v for k, v in entity_totals.items() if v > 0}
            col1, col2 = st.columns([3, 2])
            with col1:
                fig = create_bar_chart(filtered_entities, "Complaints by Entity", horizontal=True, color="#2563EB")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig_donut = create_donut_chart(filtered_entities, "Entity Proportions")
                st.plotly_chart(fig_donut, use_container_width=True)
        else:
            empty_chart_placeholder("Complaints by Entity")
            st.info("ℹ️ Detail cells are unpopulated in this workbook. Geographic analysis will appear once figures are present.")

    elif format_type == "standard_tabular":
        df = data_bundle.get("tabular_df")
        mapping = data_bundle.get("mapping", {})
        dist_col = mapping.get("district")
        prov_col = mapping.get("province")
        reg_col = mapping.get("region")
        stat_col = mapping.get("status")

        if not dist_col and not prov_col and not reg_col:
            st.warning("⚠️ **No Geographical Dimensions Mapped:** The uploaded dataset does not contain mapped District, Province, or Region fields. In compliance with Zero-Tolerance guidelines, geographical charts are disabled to prevent statistical hallucination.")
            return

        # District KPI Cards
        total_districts = df[dist_col].nunique() if dist_col and dist_col in df.columns else 0
        top_district = df[dist_col].mode()[0] if dist_col and dist_col in df.columns and not df[dist_col].empty else "N/A"
        
        cards = [
            render_kpi_card("Total Districts", total_districts, "Distinct districts in file", dist_col or "", "blue"),
            render_kpi_card("Highest Volume District", top_district, "District with most grievances", dist_col or "", "indigo"),
            render_kpi_card("Operational Region", df[reg_col].iloc[0] if reg_col and reg_col in df.columns else "Verified Territory", "Dataset region tag", reg_col or "", "teal"),
        ]
        render_kpi_grid(cards)

        # ── Two Key Bar Charts for Geographic Section ──
        col1, col2 = st.columns(2)
        if dist_col and dist_col in df.columns:
            dist_counts = df[dist_col].dropna().value_counts().to_dict()
            with col1:
                st.plotly_chart(create_bar_chart(dist_counts, f"Total Complaints by District ({dist_col})", color="#2563EB"), use_container_width=True)

            # Resolution Rate by District
            if stat_col and stat_col in df.columns:
                clean_geo = df.dropna(subset=[dist_col, stat_col])
                dist_res = {}
                for d, group in clean_geo.groupby(dist_col):
                    res_c = group[stat_col].astype(str).str.lower().str.contains("resolve|closed").sum()
                    rate = (res_c / len(group) * 100) if len(group) > 0 else 0
                    dist_res[d] = round(rate, 1)
                
                with col2:
                    st.plotly_chart(create_bar_chart(dist_res, "Resolution Rate (%) by District", y_label="Resolution %", color="#0D9488", is_percentage=True), use_container_width=True)

        # ── Detailed Geographic Summary Table (No Empty Rows) ──
        if dist_col and dist_col in df.columns and stat_col and stat_col in df.columns:
            st.markdown("### 📋 District Performance & Workflow Matrix")
            clean_df = df.dropna(subset=[dist_col, stat_col])
            
            geo_summary = clean_df.groupby(dist_col).agg(
                Total_Complaints=(clean_df.columns[0], 'count'),
                Resolved=(stat_col, lambda s: s.astype(str).str.lower().str.contains("resolve|closed").sum()),
                Forwarded=(stat_col, lambda s: s.astype(str).str.lower().str.contains("forward").sum()),
                Escalated=(stat_col, lambda s: s.astype(str).str.lower().str.contains("escalat").sum()),
                Response_Awaited=(stat_col, lambda s: s.astype(str).str.lower().str.contains("await|pending").sum()),
            ).reset_index()

            geo_summary["Resolution_Rate"] = (geo_summary["Resolved"] / geo_summary["Total_Complaints"] * 100).round(1).astype(str) + "%"
            geo_summary = geo_summary.sort_values(by="Total_Complaints", ascending=False)
            
            # Remove any empty or zero rows
            geo_summary = geo_summary[geo_summary["Total_Complaints"] > 0]
            st.dataframe(geo_summary, use_container_width=True, hide_index=True)
