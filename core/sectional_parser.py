"""
PMDU Sectional Matrix Parser:
Extracts multi-section matrix reports (Forwarded, Escalated, Reopened, Response Awaited).
Preserves formulas, cached values, merged total columns, and supports user configuration
of unpopulated row and column headers without inventing data.
"""
from typing import Dict, Any, List, Optional
import openpyxl
import re
import pandas as pd
import numpy as np

def parse_pmdu_sectional_workbook(
    file_path_or_bytes,
    sheet_name: Optional[str] = None,
    column_labels: Optional[List[str]] = None,
    row_labels_map: Optional[Dict[str, List[str]]] = None
) -> Dict[str, Any]:
    """
    Parses a PMDU 4-section matrix workbook.
    Extracts:
    - Metadata: Report Title, Region, As-of Date
    - Sections: Forwarded, Escalated, Reopened, Response Awaited
    - Detail rows, row totals, column totals, grand totals
    - Both raw formulas and evaluated cached values
    - Allows user-supplied column_labels and row_labels_map without hallucination
    """
    try:
        # 1. Load formula workbook and value workbook
        if hasattr(file_path_or_bytes, "seek"):
            file_path_or_bytes.seek(0)
        wb_formula = openpyxl.load_workbook(file_path_or_bytes, data_only=False)
        
        if hasattr(file_path_or_bytes, "seek"):
            file_path_or_bytes.seek(0)
        wb_values = openpyxl.load_workbook(file_path_or_bytes, data_only=True)

        sheets = wb_formula.sheetnames
        target_sheet = sheet_name if (sheet_name and sheet_name in sheets) else sheets[0]
        
        ws_form = wb_formula[target_sheet]
        ws_val = wb_values[target_sheet]

        max_r = max(ws_form.max_row, ws_val.max_row)
        max_c = max(ws_form.max_column, ws_val.max_column)

        # 2. Extract Title and Metadata from Header Rows (rows 1-3)
        raw_title = ""
        region = "Unknown Region"
        as_of_date = "Unknown Date"

        for r in range(1, min(max_r + 1, 5)):
            for c in range(1, min(max_c + 1, 10)):
                v = ws_val.cell(r, c).value
                if v and isinstance(v, str) and "PMDU" in v:
                    raw_title = v.strip()
                    break
            if raw_title:
                break

        if raw_title:
            # Extract date if present (e.g. 13.11.2026 or 13/11/2026 or 2026-11-13)
            date_match = re.search(r'(\d{1,2}[\.\/\-]\d{1,2}[\.\/\-]\d{2,4})', raw_title)
            if date_match:
                as_of_date = date_match.group(1)
            
            # Extract Region (e.g. 'Rawalpindi Region')
            reg_match = re.search(r'([A-Za-z]+(?:\s+[A-Za-z]+)*\s+Region)', raw_title, re.IGNORECASE)
            if reg_match:
                extracted = reg_match.group(1).strip()
                # Remove leading 'of ' or 'PMDU Complaints of '
                extracted = re.sub(r'^(?:PMDU\s+Complaints\s+of\s+|of\s+)', '', extracted, flags=re.IGNORECASE)
                region = extracted
            elif "Rawalpindi" in raw_title:
                region = "Rawalpindi Region"

        # 3. Locate the Section Headers
        # Target Sections
        target_sections = [
            "Forwarded Complaints",
            "Escalated Complaints",
            "Reopened Complaints",
            "Response Awaited Complaints"
        ]

        section_locations = []
        for r in range(1, max_r + 1):
            val_b = ws_val.cell(r, 2).value  # Column B
            if val_b and isinstance(val_b, str):
                vb_clean = val_b.strip()
                for ts in target_sections:
                    if ts.lower() in vb_clean.lower():
                        section_locations.append({
                            "name": ts,
                            "header_row": r,
                            "raw_label": vb_clean
                        })
                        break

        # 4. Detail Columns C to M (11 columns)
        # Check if user passed custom labels, otherwise default to neutral Column C..M
        default_col_labels = [f"Entity_{chr(65+i)}" for i in range(2, 13)] # C to M
        active_col_labels = column_labels if (column_labels and len(column_labels) == 11) else default_col_labels

        sections_data = {}
        all_discrepancies = []

        for idx, sec in enumerate(section_locations):
            sec_name = sec["name"]
            h_row = sec["header_row"]
            
            # Find the 'Total' row for this section
            total_row = None
            next_h_row = section_locations[idx + 1]["header_row"] if idx + 1 < len(section_locations) else max_r + 1
            
            for r in range(h_row + 1, next_h_row):
                cell_val = ws_val.cell(r, 2).value
                if cell_val and isinstance(cell_val, str) and "total" in cell_val.strip().lower():
                    total_row = r
                    break
            
            if total_row is None:
                # If no explicit Total row found, assume up to next_h_row - 1
                total_row = next_h_row - 1

            detail_start_row = h_row + 1
            detail_end_row = total_row - 1
            num_detail_rows = max(0, detail_end_row - detail_start_row + 1)

            # Get user-provided row labels for this section if any
            custom_row_labels = None
            if row_labels_map and sec_name in row_labels_map:
                custom_row_labels = row_labels_map[sec_name]

            # Parse Detail Rows
            detail_records = []
            row_totals_calc = []
            row_totals_source = []

            for r_idx, r in enumerate(range(detail_start_row, detail_end_row + 1)):
                raw_row_label = ws_val.cell(r, 2).value
                if custom_row_labels and r_idx < len(custom_row_labels):
                    row_label = custom_row_labels[r_idx]
                elif raw_row_label is not None and str(raw_row_label).strip() != "":
                    row_label = str(raw_row_label).strip()
                else:
                    row_label = f"Subcategory_{r_idx + 1}"

                # Columns C to M (columns 3 to 13)
                detail_values = []
                for c in range(3, 14):
                    c_val = ws_val.cell(r, c).value
                    # Store exact value without silently converting None to 0
                    detail_values.append(c_val)

                # Total in Col N (col 14)
                src_formula = ws_form.cell(r, 14).value
                src_val = ws_val.cell(r, 14).value
                
                # Calculate independent row sum (ignoring None / blank)
                numeric_vals = [float(v) for v in detail_values if isinstance(v, (int, float)) and not np.isnan(v)]
                calc_sum = sum(numeric_vals) if numeric_vals else None

                detail_records.append({
                    "row_index": r,
                    "row_label": row_label,
                    "values": detail_values, # list of 11 values
                    "source_total_val": src_val,
                    "source_total_formula": str(src_formula) if src_formula else None,
                    "calculated_total": calc_sum,
                    "has_data": len(numeric_vals) > 0
                })

            # Parse Section Total Row
            col_totals_source = []
            col_totals_formula = []
            col_totals_calc = []

            for col_idx, c in enumerate(range(3, 14)):
                s_form = ws_form.cell(total_row, c).value
                s_val = ws_val.cell(total_row, c).value
                
                # Calculate column sum
                col_num_vals = []
                for rec in detail_records:
                    v = rec["values"][col_idx]
                    if isinstance(v, (int, float)) and not np.isnan(v):
                        col_num_vals.append(float(v))
                
                c_sum = sum(col_num_vals) if col_num_vals else None
                
                col_totals_source.append(s_val)
                col_totals_formula.append(str(s_form) if s_form else None)
                col_totals_calc.append(c_sum)

            # Grand Total Cell (Row total_row, Col 14)
            gt_source_val = ws_val.cell(total_row, 14).value
            gt_source_formula = str(ws_form.cell(total_row, 14).value)
            
            # Calculate grand total from calculated row sums
            valid_row_totals = [r["calculated_total"] for r in detail_records if r["calculated_total"] is not None]
            gt_calc = sum(valid_row_totals) if valid_row_totals else None

            # Discrepancy check
            if gt_source_val is not None and gt_calc is not None:
                if abs(float(gt_source_val) - float(gt_calc)) > 1e-4:
                    all_discrepancies.append({
                        "section": sec_name,
                        "type": "Grand Total Mismatch",
                        "source": gt_source_val,
                        "calculated": gt_calc,
                        "difference": gt_calc - float(gt_source_val)
                    })

            sections_data[sec_name] = {
                "header_row": h_row,
                "total_row": total_row,
                "detail_rows_count": num_detail_rows,
                "detail_records": detail_records,
                "column_labels": active_col_labels,
                "col_totals_source": col_totals_source,
                "col_totals_calc": col_totals_calc,
                "col_totals_formula": col_totals_formula,
                "grand_total_source": gt_source_val,
                "grand_total_calculated": gt_calc,
                "grand_total_formula": gt_source_formula,
                "is_populated": any(r["has_data"] for r in detail_records)
            }

        wb_formula.close()
        wb_values.close()

        # Check overall dataset population
        any_populated = any(s["is_populated"] for s in sections_data.values())

        return {
            "success": True,
            "format": "pmdu_sectional",
            "sheet_name": target_sheet,
            "title": raw_title or "PMDU Complaints Report",
            "region": region,
            "as_of_date": as_of_date,
            "column_labels": active_col_labels,
            "sections": sections_data,
            "is_populated": any_populated,
            "discrepancies": all_discrepancies,
            "total_sections": len(sections_data)
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to parse PMDU sectional matrix: {str(e)}"}


def sectional_to_flat_dataframe(sectional_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Transforms PMDU Sectional parsed data into a standard flat DataFrame
    for consistent filtering, charting, and tabular inspection.
    """
    rows = []
    col_labels = sectional_data.get("column_labels", [f"Col_{i+1}" for i in range(11)])
    region = sectional_data.get("region", "Rawalpindi Region")
    as_of_date = sectional_data.get("as_of_date", "13.11.2026")

    for sec_name, sec in sectional_data.get("sections", {}).items():
        for rec in sec.get("detail_records", []):
            row_label = rec["row_label"]
            for col_idx, val in enumerate(rec["values"]):
                col_name = col_labels[col_idx] if col_idx < len(col_labels) else f"Entity_{col_idx+1}"
                rows.append({
                    "Section": sec_name,
                    "Row_Label": row_label,
                    "Column_Entity": col_name,
                    "Complaint_Count": val, # Can be None or numeric
                    "Region": region,
                    "Reporting_Date": as_of_date,
                    "Source_Total_Formula": rec.get("source_total_formula")
                })
    return pd.DataFrame(rows)
