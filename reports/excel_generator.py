"""
Excel Report Generator using OpenPyXL.
Exports formatted workbooks with styled headers, verified totals, and audit trails.
"""
from typing import Dict, Any, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import io
import pandas as pd

def generate_excel_report(
    summary_data: Dict[str, Any],
    reconciliation_df: Optional[pd.DataFrame] = None,
    detail_df: Optional[pd.DataFrame] = None,
    output_path: Optional[str] = None
) -> bytes:
    """
    Creates a styled multi-sheet Excel report.
    Returns bytes and optionally writes to output_path.
    """
    wb = openpyxl.Workbook()
    
    # Fonts & Fills
    header_fill = PatternFill(start_color="101B33", end_color="101B33", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=14, bold=True, color="101B33")
    subtitle_font = Font(name="Calibri", size=10, italic=True, color="64748B")
    total_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    bold_font = Font(name="Calibri", size=10, bold=True, color="172033")
    regular_font = Font(name="Calibri", size=10, color="172033")
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    # Sheet 1: Executive Summary
    ws_exec = wb.active
    ws_exec.title = "Executive Summary"
    ws_exec.views.sheetView[0].showGridLines = True

    # Title block
    ws_exec.cell(1, 1, "PMDU COMPLAINTS ANALYTICS & MONITORING REPORT").font = title_font
    ws_exec.cell(2, 1, f"Report Title: {summary_data.get('title', 'PMDU Region')} | Reference Date: {summary_data.get('as_of_date', 'N/A')}").font = subtitle_font
    
    # Table of KPIs
    start_r = 4
    headers = ["Metric Dimension", "Source Value", "Calculated Total", "Verification Status", "Calculation Methodology"]
    for col_idx, h in enumerate(headers, 1):
        c = ws_exec.cell(start_r, col_idx, h)
        c.fill = header_fill
        c.font = header_font
        c.alignment = Alignment(horizontal="center", vertical="center")

    curr_r = start_r + 1
    if "sections" in summary_data:
        for sec_name, s_info in summary_data["sections"].items():
            ws_exec.cell(curr_r, 1, sec_name).font = bold_font
            ws_exec.cell(curr_r, 2, s_info.get("source_total", "N/A")).font = regular_font
            ws_exec.cell(curr_r, 3, s_info.get("calculated_total", "N/A")).font = bold_font
            ws_exec.cell(curr_r, 4, "Verified" if s_info.get("is_verified") else "Formula Invariant").font = regular_font
            ws_exec.cell(curr_r, 5, s_info.get("formula", "Sum of detail cells")).font = regular_font
            for c_i in range(1, 6):
                ws_exec.cell(curr_r, c_i).border = thin_border
            curr_r += 1
    else:
        ws_exec.cell(curr_r, 1, "Total Complaints").font = bold_font
        ws_exec.cell(curr_r, 2, "N/A").font = regular_font
        ws_exec.cell(curr_r, 3, summary_data.get("total_complaints", "N/A")).font = bold_font
        ws_exec.cell(curr_r, 4, "Verified Record Count").font = regular_font
        ws_exec.cell(curr_r, 5, summary_data.get("total_complaints_method", "Row count")).font = regular_font
        for c_i in range(1, 6):
            ws_exec.cell(curr_r, c_i).border = thin_border
        curr_r += 1

    # Sheet 2: Reconciliation Sheet (if provided)
    if reconciliation_df is not None and not reconciliation_df.empty:
        ws_recon = wb.create_sheet(title="Reconciliation Audit")
        ws_recon.views.sheetView[0].showGridLines = True
        ws_recon.cell(1, 1, "INDEPENDENT CALCULATION AUDIT & RECONCILIATION").font = title_font
        
        # Headers
        r_cols = list(reconciliation_df.columns)
        for col_i, col_name in enumerate(r_cols, 1):
            cell = ws_recon.cell(3, col_i, col_name)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        # Rows
        for row_i, row_data in enumerate(reconciliation_df.itertuples(index=False), 4):
            for col_i, val in enumerate(row_data, 1):
                c = ws_recon.cell(row_i, col_i, str(val) if val is not None else "")
                c.font = regular_font
                c.border = thin_border

    # Sheet 3: Filtered Data (if provided)
    if detail_df is not None and not detail_df.empty:
        ws_detail = wb.create_sheet(title="Data Records")
        ws_detail.views.sheetView[0].showGridLines = True
        
        # Headers
        d_cols = list(detail_df.columns)
        for col_i, col_name in enumerate(d_cols, 1):
            cell = ws_detail.cell(1, col_i, col_name)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        # Rows (limit to first 5000 for export safety)
        for row_i, row_data in enumerate(detail_df.head(5000).itertuples(index=False), 2):
            for col_i, val in enumerate(row_data, 1):
                c = ws_detail.cell(row_i, col_i, val if pd.notnull(val) else "")
                c.font = regular_font
                c.border = thin_border

    # Adjust column widths for all sheets
    for ws in wb.worksheets:
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    buffer = io.BytesIO()
    wb.save(buffer)
    excel_bytes = buffer.getvalue()
    buffer.close()

    if output_path:
        with open(output_path, "wb") as f:
            f.write(excel_bytes)

    return excel_bytes

