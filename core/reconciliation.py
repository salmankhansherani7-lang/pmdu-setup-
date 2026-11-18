"""
Reconciliation & Audit Engine:
Independently verifies every calculation against source data and formulas.
Flags any discrepancies with full mathematical audit trail.
"""
from typing import Dict, Any, List
import pandas as pd

def build_sectional_reconciliation_table(sectional_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Constructs an audit table for PMDU Sectional Reports:
    - Section Name
    - Granular Item (Grand Total or Row Total)
    - Source Value (from Excel cell/cache)
    - Calculated Value (summed independently from raw detail cells)
    - Difference
    - Source Formula
    - Verification Status (VERIFIED, MISMATCH, UNPOPULATED)
    """
    records = []
    sections = sectional_data.get("sections", {})

    for sec_name, s_data in sections.items():
        # 1. Section Grand Total
        gt_source = s_data.get("grand_total_source")
        gt_calc = s_data.get("grand_total_calculated")
        gt_form = s_data.get("grand_total_formula")
        
        diff = None
        status = "UNPOPULATED"
        
        if gt_calc is not None and gt_source is not None:
            try:
                diff = round(gt_calc - float(gt_source), 4)
                status = "VERIFIED" if abs(diff) < 1e-4 else "MISMATCH"
            except Exception:
                status = "EVALUATION_ERROR"
        elif gt_calc is not None and gt_source is None:
            status = "CALCULATED_ONLY"
        elif gt_source == 0 and gt_calc is None:
            status = "UNPOPULATED_TEMPLATE (0 in source, no detail figures)"

        records.append({
            "Section": sec_name,
            "Item": "Section Grand Total",
            "Source Value": gt_source if gt_source is not None else "None",
            "Calculated Value": gt_calc if gt_calc is not None else "None",
            "Difference": diff if diff is not None else "N/A",
            "Formula in Excel": gt_form or "None",
            "Verification Status": status
        })

        # 2. Detail Row Totals
        for rec in s_data.get("detail_records", []):
            r_source = rec.get("source_total_val")
            r_calc = rec.get("calculated_total")
            r_form = rec.get("source_total_formula")
            
            r_diff = None
            r_status = "UNPOPULATED"
            if r_calc is not None and r_source is not None:
                try:
                    r_diff = round(r_calc - float(r_source), 4)
                    r_status = "VERIFIED" if abs(r_diff) < 1e-4 else "MISMATCH"
                except Exception:
                    r_status = "EVALUATION_ERROR"
            elif r_calc is not None and r_source is None:
                r_status = "CALCULATED_ONLY"
            elif r_source == 0 and r_calc is None:
                r_status = "UNPOPULATED"

            records.append({
                "Section": sec_name,
                "Item": f"Row: {rec['row_label']}",
                "Source Value": r_source if r_source is not None else "None",
                "Calculated Value": r_calc if r_calc is not None else "None",
                "Difference": r_diff if r_diff is not None else "N/A",
                "Formula in Excel": r_form or "None",
                "Verification Status": r_status
            })

    return pd.DataFrame(records)

