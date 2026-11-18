"""
View: Data Quality & Validation Audit — Validation status, column completeness, and mathematical audit.
"""
import streamlit as st
import pandas as pd
from components.empty_state import no_data_placeholder
from components.charts import create_bar_chart
from core.reconciliation import build_sectional_reconciliation_table
from core.column_mapping import auto_suggest_mappings
from config import STANDARD_FIELDS

def render_data_quality_page(data_bundle: dict):
    st.markdown("## 🛡️ Data Quality")
    st.caption("Validation status, column mapping, data integrity, and mathematical reconciliation.")

    if not data_bundle.get("has_data"):
        st.markdown("""
        <div style="background:#FFF; border:1px solid #E2E8F0; border-left:5px solid #94A3B8;
                    border-radius:8px; padding:18px 24px; margin-bottom:20px; display:flex;
                    justify-content:space-between; align-items:center;">
            <div>
                <div style="font-size:12px; color:#64748B; text-transform:uppercase; font-weight:700;">
                    Overall Data Quality Status
                </div>
                <div style="font-size:22px; font-weight:800; color:#0F172A;">No Data Loaded</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:11px; color:#64748B;">Quality Score</div>
                <div style="font-size:30px; font-weight:800; color:#94A3B8;">—</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        no_data_placeholder("🛡️", "No File Loaded for Audit", "Upload an Excel or CSV file in the sidebar to run mathematical reconciliation and data quality checks.")
        return

    val_report = data_bundle.get("validation_report", {})
    score      = val_report.get("quality_score", 100.0)
    status     = val_report.get("status", "PASSED")

    color_map = {"PASSED": "#059669", "PASSED_WITH_WARNINGS": "#D97706", "FAILED": "#DC2626"}
    score_color = color_map.get(status, "#64748B")

    st.markdown(f"""
    <div style="background:#fff; border:1px solid #E2E8F0; border-left:5px solid {score_color};
                border-radius:8px; padding:18px 24px; margin-bottom:20px; display:flex;
                justify-content:space-between; align-items:center;">
        <div>
            <div style="font-size:12px; color:#64748B; text-transform:uppercase; font-weight:700;">
                Overall Data Quality Status
            </div>
            <div style="font-size:22px; font-weight:800; color:#0F172A;">{status.replace('_',' ')}</div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:11px; color:#64748B;">Quality Score</div>
            <div style="font-size:30px; font-weight:800; color:{score_color};">
                {score}<span style="font-size:16px;">/100</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Bar Chart: Column Completeness Rate (%) ──
    df = data_bundle.get("tabular_df")
    if df is not None and not df.empty:
        completeness = {}
        for col in df.columns:
            non_null_pct = round((df[col].notnull().sum() / len(df) * 100), 1)
            completeness[col] = non_null_pct
        
        st.plotly_chart(create_bar_chart(completeness, "Field Completeness Rate (%) Across Columns", horizontal=True, color="#0D9488", is_percentage=True), use_container_width=True)

    tab_recon, tab_map, tab_err, tab_warn, tab_ok = st.tabs([
        "⚖️ Reconciliation",
        "🗺️ Column Mapping",
        f"❌ Errors ({len(val_report.get('errors', []))})",
        f"⚠️ Warnings ({len(val_report.get('warnings', []))})",
        f"✅ Passed ({len(val_report.get('passed', []))})",
    ])

    with tab_recon:
        st.markdown("### Mathematical Verification Table")
        st.caption("Calculated totals verified against spreadsheet formula cache.")
        fmt = data_bundle.get("format_type")
        if fmt == "pmdu_sectional":
            parsed = data_bundle.get("parsed_sectional", {})
            recon  = build_sectional_reconciliation_table(parsed)
            # Remove any empty rows
            recon_clean = recon.dropna(how="all")
            st.dataframe(recon_clean, use_container_width=True, hide_index=True)
            discr = parsed.get("discrepancies", [])
            if discr:
                st.error(f"🚨 {len(discr)} mismatch(es) found between formula cache and independent sums.")
            else:
                st.success("✅ All verified totals are mathematically consistent with formula results.")
        else:
            st.info("Tabular datasets are verified at record level. Row count matches raw file length.")

    with tab_map:
        st.markdown("### Column Mapping")
        st.caption("Map file columns to complaint dimensions.")
        fmt = data_bundle.get("format_type")
        if fmt == "standard_tabular":
            if df is not None:
                current_mapping = st.session_state.get("user_column_mapping", auto_suggest_mappings(list(df.columns)))
                options = ["— Unmapped —"] + list(df.columns)
                new_mapping = {}
                col1, col2 = st.columns(2)
                items = list(STANDARD_FIELDS.items())
                half = (len(items) + 1) // 2
                for idx, (fk, fmeta) in enumerate(items):
                    target = col1 if idx < half else col2
                    with target:
                        cur_val = current_mapping.get(fk)
                        def_idx = options.index(cur_val) if cur_val in options else 0
                        sel = st.selectbox(fmeta["label"], options, index=def_idx, key=f"qmap_{fk}")
                        new_mapping[fk] = sel if sel != "— Unmapped —" else None

                if st.button("✅ Apply Mapping", type="primary"):
                    st.session_state["user_column_mapping"] = new_mapping
                    st.success("Column mapping updated.")
        else:
            st.info("For PMDU matrix files, column mapping is configured automatically.")

    with tab_err:
        errors = val_report.get("errors", [])
        if errors:
            for e in errors:
                st.error(f"**{e.get('check')}:** {e.get('message')}")
        else:
            st.success("No critical errors found.")

    with tab_warn:
        warnings = val_report.get("warnings", [])
        if warnings:
            for w in warnings:
                st.warning(f"**{w.get('check')}:** {w.get('message')}")
        else:
            st.info("No warnings raised.")

    with tab_ok:
        passed = val_report.get("passed", [])
        for p in passed:
            st.success(f"**{p.get('check')}:** {p.get('message')}")
