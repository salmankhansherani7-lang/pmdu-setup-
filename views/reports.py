"""
View: Reports & Downloads — Executive PDF briefing and verified Excel audit workbooks.
"""
import streamlit as st
from datetime import datetime
from components.empty_state import no_data_placeholder
from components.charts import create_bar_chart
from reports.pdf_generator import generate_pdf_report
from reports.excel_generator import generate_excel_report
from core.reconciliation import build_sectional_reconciliation_table

def render_reports_page(data_bundle: dict):
    st.markdown("## 📥 Reports")
    st.caption("Generate official executive PDF briefings and mathematically audited Excel workbooks.")

    if not data_bundle.get("has_data"):
        no_data_placeholder("📥", "No Data Available for Reports", "Upload an Excel or CSV file in the sidebar to enable PDF and Excel report generation.")
        return

    dataset_name = data_bundle.get("dataset_name", "Uploaded Dataset")
    format_type  = data_bundle.get("format_type")
    summary_info = (
        data_bundle.get("sectional_metrics", {})
        if format_type == "pmdu_sectional"
        else data_bundle.get("tabular_metrics", {})
    )

    # Document parameters card
    st.markdown(f"""
    <div class="content-box">
        <div class="content-box-header">Report Parameters &amp; Verification Metadata</div>
        <div style="display:grid; grid-template-columns: repeat(auto-fit,minmax(200px,1fr)); gap:12px; font-size:13px;">
            <div><b>Source Dataset:</b><br/>{dataset_name}</div>
            <div><b>Audit Timestamp:</b><br/>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
            <div><b>Structure:</b><br/>{'Sectional Matrix' if format_type == 'pmdu_sectional' else 'Tabular Dataset'}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Bar Chart for Reports View: Top Departmental Volume Snapshot ──
    df = data_bundle.get("tabular_df")
    mapping = data_bundle.get("mapping", {})
    dept_col = mapping.get("department") if mapping else None
    if df is not None and dept_col and dept_col in df.columns:
        dept_dist = df[dept_col].dropna().value_counts().head(8).to_dict()
        st.plotly_chart(create_bar_chart(dept_dist, "Report Benchmark: Complaints by Department", horizontal=True, color="#2563EB"), use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📑 PDF Executive Briefing")
        st.write("Formal government-style briefing document with verified KPI tables, methodology, and signatures.")
        if st.button("🔄 Generate PDF", use_container_width=True, key="btn_pdf", type="primary"):
            with st.spinner("Building PDF…"):
                try:
                    pdf = generate_pdf_report(summary_info, dataset_name=dataset_name)
                    st.session_state["cached_pdf_bytes"] = pdf
                    st.success("PDF ready for download.")
                except Exception as e:
                    st.error(f"PDF generation failed: {e}")

        if "cached_pdf_bytes" in st.session_state:
            st.download_button(
                "📥 Download PDF Document",
                data=st.session_state["cached_pdf_bytes"],
                file_name=f"PMDU_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    with col2:
        st.markdown("### 📊 Excel Audit Workbook")
        st.write("Multi-sheet audit workbook: Executive KPI Summary, Reconciliation Audit, and Complete Records.")
        if st.button("🔄 Generate Excel", use_container_width=True, key="btn_excel", type="primary"):
            with st.spinner("Building Excel workbook…"):
                try:
                    recon_df = None
                    if format_type == "pmdu_sectional":
                        recon_df = build_sectional_reconciliation_table(data_bundle.get("parsed_sectional", {}))
                    detail_df = data_bundle.get("flat_df") if format_type == "pmdu_sectional" else data_bundle.get("tabular_df")
                    if detail_df is not None:
                        detail_df = detail_df.dropna(how="all")
                    xlsx = generate_excel_report(summary_info, reconciliation_df=recon_df, detail_df=detail_df)
                    st.session_state["cached_excel_bytes"] = xlsx
                    st.success("Excel ready for download.")
                except Exception as e:
                    st.error(f"Excel generation failed: {e}")

        if "cached_excel_bytes" in st.session_state:
            st.download_button(
                "📥 Download Excel Workbook",
                data=st.session_state["cached_excel_bytes"],
                file_name=f"PMDU_Audit_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    st.markdown("---")
    st.markdown("### Methodology & Integrity Notes")
    st.markdown("""
    1. Computations run exclusively on in-memory buffers — the original uploaded spreadsheet is never altered.
    2. Totals are independently recalculated from granular cells and cross-audited.
    3. Resolution Rate is only calculated from explicit status disposal values in the source dataset.
    4. Missing values are never silently replaced with zero.
    """)
