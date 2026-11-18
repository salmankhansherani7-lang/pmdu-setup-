"""
Excel inspection and extraction engine.
Preserves original files, extracts sheet metadata, detects merged cells,
and reads both raw formulas and cached evaluated values.
"""
from typing import Dict, Any, List, Optional
import openpyxl
import pandas as pd
import os
import io

def get_excel_sheets(file_path_or_bytes) -> List[str]:
    """Returns list of sheet names in the workbook."""
    wb = openpyxl.load_workbook(file_path_or_bytes, read_only=True)
    sheets = wb.sheetnames
    wb.close()
    return sheets

def read_excel_tabular(
    file_path_or_bytes,
    sheet_name: Optional[str] = None,
    header_row_idx: int = 0
) -> Dict[str, Any]:
    """
    Reads an Excel worksheet as a standard tabular dataset with user-selectable header row.
    Never alters source file.
    """
    try:
        if hasattr(file_path_or_bytes, "seek"):
            file_path_or_bytes.seek(0)
            
        wb_data = openpyxl.load_workbook(file_path_or_bytes, data_only=True)
        sheets = wb_data.sheetnames
        selected_sheet = sheet_name if (sheet_name and sheet_name in sheets) else sheets[0]
        ws_data = wb_data[selected_sheet]

        # Read all rows into matrix
        all_rows = list(ws_data.iter_rows(values_only=True))
        wb_data.close()

        if not all_rows:
            return {"success": False, "error": "Worksheet contains no data"}

        # Validate header row index
        if header_row_idx >= len(all_rows):
            header_row_idx = 0

        raw_headers = all_rows[header_row_idx]
        data_rows = all_rows[header_row_idx + 1:]

        # Clean header names (handle None or duplicate headers)
        headers = []
        for i, h in enumerate(raw_headers):
            if h is None or str(h).strip() == "":
                headers.append(f"Column_{i+1}")
            else:
                col_name = str(h).strip()
                # De-duplicate if needed
                if col_name in headers:
                    headers.append(f"{col_name}_{i+1}")
                else:
                    headers.append(col_name)

        # Build DataFrame
        df = pd.DataFrame(data_rows, columns=headers)
        
        # Drop rows and columns that are entirely blank
        df.dropna(how="all", inplace=True)
        df.dropna(axis=1, how="all", inplace=True)

        return {
            "success": True,
            "dataframe": df,
            "preview": df.head(50),
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": list(df.columns),
            "sheet_name": selected_sheet,
            "all_sheets": sheets,
            "missing_summary": df.isnull().sum().to_dict(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to read Excel worksheet: {str(e)}"}

