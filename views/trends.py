"""
View: Trends & Longitudinal Comparisons — Temporal trajectory and period-over-period dynamics.
"""
import streamlit as st
import pandas as pd
from components.charts import create_line_chart, create_bar_chart, create_grouped_bar_chart
from components.empty_state import no_data_placeholder, empty_chart_placeholder
from components.kpi_cards import render_kpi_card, render_kpi_grid

def render_trends_page(data_bundle: dict):
    st.markdown("## 📈 Trends & Comparisons")
    st.caption("Temporal trajectory, seasonal peaks, and period-over-period change analytics.")

    if not data_bundle.get("has_data"):
        no_data_placeholder("📈", "No Trend Data Available", "Upload an Excel or CSV file in the sidebar to view longitudinal trends.")
        return

    format_type = data_bundle.get("format_type")

    if format_type == "pmdu_sectional":
        as_of_date = data_bundle.get("parsed_sectional", {}).get("as_of_date", "")
        if as_of_date and as_of_date != "Unknown Date":
            st.info(f"ℹ️ **Reporting Horizon Notice:** The uploaded PMDU matrix report represents a point-in-time snapshot as of **{as_of_date}**.")
        
        flat_df = data_bundle.get("flat_df")
        if flat_df is not None and not flat_df.empty:
            valid_counts = flat_df.dropna(subset=["Complaint_Count"])
            valid_counts = valid_counts[valid_counts["Complaint_Count"] > 0]
            if not valid_counts.empty:
                st.plotly_chart(create_grouped_bar_chart(
                    valid_counts,
                    x_col="Column_Entity",
                    y_col="Complaint_Count",
                    group_col="Section",
                    title="Volume by Entity Across Workflow Sections"
                ), use_container_width=True)
            else:
                empty_chart_placeholder("Volume Across Workflow Sections")
                st.info("ℹ️ Detail cells are unpopulated. Cross-sectional trends will populate once figures are present.")

    elif format_type == "standard_tabular":
        df = data_bundle.get("tabular_df")
        mapping = data_bundle.get("mapping", {})
        sub_col = mapping.get("submission_date")
        res_col = mapping.get("resolution_date")
        dept_col = mapping.get("department")

        if not sub_col or sub_col not in df.columns:
            st.warning("⚠️ **No Submission Date Mapped:** Time-series trends require a valid mapped Date column. Dates are not assumed.")
            return

        temp_dates = pd.to_datetime(df[sub_col], errors="coerce")
        valid_df = df[temp_dates.notnull()].copy()
        if valid_df.empty:
            st.warning("⚠️ No valid dates could be parsed from the mapped submission date column.")
            return

        valid_df["parsed_date"] = temp_dates[temp_dates.notnull()]
        valid_df["month_year"] = valid_df["parsed_date"].dt.to_period("M").astype(str)
        monthly_counts = valid_df["month_year"].value_counts().sort_index().to_dict()

        peak_month = max(monthly_counts, key=monthly_counts.get) if monthly_counts else "N/A"
        peak_volume = monthly_counts.get(peak_month, 0)
        total_months = len(monthly_counts)

        cards = [
            render_kpi_card("Reporting Horizon", f"{total_months} Months", "Active observation window", f"{min(monthly_counts)} → {max(monthly_counts)}", "blue"),
            render_kpi_card("Peak Inflow Month", peak_month, "Highest complaint volume", f"{peak_volume} complaints", "amber"),
            render_kpi_card("Monthly Average", f"{round(len(valid_df)/max(1, total_months), 1)}", "Average cases per month", "Total ÷ Months", "teal"),
        ]
        render_kpi_grid(cards)

        # ── Two Key Bar / Trend Charts for Trends Section ──
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_bar_chart(monthly_counts, "Monthly Inflow Volume (Bar Chart)", x_label="Month", y_label="Complaints Lodged", color="#2563EB"), use_container_width=True)

        with col2:
            # Average days to resolution by department if resolution_date exists
            if res_col and res_col in valid_df.columns and dept_col and dept_col in valid_df.columns:
                valid_df["res_parsed"] = pd.to_datetime(valid_df[res_col], errors="coerce")
                resolved_subset = valid_df[valid_df["res_parsed"].notnull()].copy()
                resolved_subset["days_to_resolve"] = (resolved_subset["res_parsed"] - resolved_subset["parsed_date"]).dt.days
                resolved_subset = resolved_subset[resolved_subset["days_to_resolve"] >= 0]
                
                if not resolved_subset.empty:
                    avg_days = resolved_subset.groupby(dept_col)["days_to_resolve"].mean().round(1).to_dict()
                    st.plotly_chart(create_bar_chart(avg_days, "Avg Resolution Time by Department (Days)", horizontal=True, color="#0D9488"), use_container_width=True)
                else:
                    st.plotly_chart(create_line_chart(monthly_counts, "Monthly Trajectory Curve", x_label="Month"), use_container_width=True)
            else:
                st.plotly_chart(create_line_chart(monthly_counts, "Monthly Trajectory Curve", x_label="Month"), use_container_width=True)

        # ── Period-Over-Period Table (No Empty Rows) ──
        st.markdown("### 📊 Period-Over-Period Change Analysis")
        trend_df = pd.DataFrame(list(monthly_counts.items()), columns=["Period", "Complaints_Count"])
        trend_df["Absolute_Change"] = trend_df["Complaints_Count"].diff().fillna(0).astype(int)
        trend_df["Percent_Change"] = (trend_df["Complaints_Count"].pct_change() * 100).round(1).fillna(0)
        trend_df["Percent_Change"] = trend_df["Percent_Change"].apply(lambda x: f"{x:+.1f}%")
        
        # Remove empty rows
        trend_df = trend_df.dropna(how="all")
        st.dataframe(trend_df, use_container_width=True, hide_index=True)
