"""
Format detector: identifies whether an uploaded dataset is a
PMDU Sectional Matrix (e.g. 4-section Rawalpindi layout) or Standard Tabular data.
"""
from typing import Dict, Any, List
import pandas as pd
import openpyxl

def detect_file_format(file_path: str, sheet_name: str = None) -> Dict[str, Any]:
    """
    Inspects file structure and determines whether it represents:
    - 'pmdu_sectional': 4-section matrix report (Forwarded, Escalated, Reopened, Response Awaited)
    - 'standard_tabular': Regular table with row/column data
    """
    if file_path.lower().endswith(".csv"):
        return {
            "format": "standard_tabular",
            "sheet_name": None,
            "sheets": [],
            "reason": "CSV files are standard flat tabular format"
        }
    
    # Inspect Excel
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True, read_only=False)
        sheets = wb.sheetnames
        target_sheet = sheet_name if (sheet_name and sheet_name in sheets) else sheets[0]
        ws = wb[target_sheet]

        # Scan first 40 rows for Sectional Keywords
        found_sections = []
        target_keywords = [
            "forwarded complaints",
            "escalated complaints",
            "reopened complaints",
            "response awaited"
        ]

        for row in ws.iter_rows(min_row=1, max_row=min(ws.max_row, 45), values_only=True):
            for cell in row:
                if cell and isinstance(cell, str):
                    c_clean = cell.strip().lower()
                    for kw in target_keywords:
                        if kw in c_clean and kw not in found_sections:
                            found_sections.append(kw)

        wb.close()

        if len(found_sections) >= 2:
            return {
                "format": "pmdu_sectional",
                "sheet_name": target_sheet,
                "sheets": sheets,
                "detected_sections": found_sections,
                "reason": f"Detected {len(found_sections)} PMDU report sections in worksheet"
            }
        else:
            return {
                "format": "standard_tabular",
                "sheet_name": target_sheet,
                "sheets": sheets,
                "reason": "Standard tabular row-column spreadsheet format"
            }
    except Exception as e:
        return {
            "format": "standard_tabular",
            "sheet_name": None,
            "sheets": [],
            "error": str(e)
        }

