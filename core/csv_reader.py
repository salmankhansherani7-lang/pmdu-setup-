"""
CSV reading and inspection engine with robust encoding & delimiter detection.
"""
from typing import Dict, Any, Tuple
import pandas as pd
import io
import os

def read_csv_safe(file_path_or_bytes, max_preview_rows: int = 50) -> Dict[str, Any]:
    """
    Safely reads CSV with multiple encoding fallbacks and delimiter detection.
    Does not modify original data.
    """
    encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
    delimiters = [",", "\t", ";", "|"]
    
    df = None
    used_encoding = None
    used_delimiter = None
    error_msg = None

    for enc in encodings:
        for sep in delimiters:
            try:
                if isinstance(file_path_or_bytes, (str, os.PathLike)):
                    with open(file_path_or_bytes, "r", encoding=enc) as f:
                        df = pd.read_csv(f, sep=sep, nrows=1000)
                elif isinstance(file_path_or_bytes, bytes):
                    df = pd.read_csv(io.BytesIO(file_path_or_bytes), sep=sep, encoding=enc, nrows=1000)
                elif hasattr(file_path_or_bytes, "seek"):
                    file_path_or_bytes.seek(0)
                    df = pd.read_csv(file_path_or_bytes, sep=sep, encoding=enc, nrows=1000)
                
                # Verify we got more than 1 column or reasonable structure
                if df is not None and df.shape[1] >= 1 and not df.empty:
                    used_encoding = enc
                    used_delimiter = sep
                    break
            except Exception as e:
                error_msg = str(e)
                continue
        if df is not None:
            break

    if df is None:
        # Load full fallback
        try:
            if hasattr(file_path_or_bytes, "seek"):
                file_path_or_bytes.seek(0)
            df = pd.read_csv(file_path_or_bytes, engine="python", on_bad_lines="skip")
        except Exception as e:
            return {"success": False, "error": f"Failed to parse CSV: {str(e)}"}

    # Load complete dataframe without truncation
    if hasattr(file_path_or_bytes, "seek"):
        file_path_or_bytes.seek(0)
        full_df = pd.read_csv(file_path_or_bytes, sep=used_delimiter or ",", encoding=used_encoding or "utf-8")
    elif isinstance(file_path_or_bytes, (str, os.PathLike)):
        full_df = pd.read_csv(file_path_or_bytes, sep=used_delimiter or ",", encoding=used_encoding or "utf-8")
    else:
        full_df = df

    return {
        "success": True,
        "dataframe": full_df,
        "preview": full_df.head(max_preview_rows),
        "total_rows": len(full_df),
        "total_columns": len(full_df.columns),
        "columns": list(full_df.columns),
        "encoding": used_encoding,
        "delimiter": used_delimiter,
        "missing_summary": full_df.isnull().sum().to_dict(),
        "dtypes": {col: str(dtype) for col, dtype in full_df.dtypes.items()}
    }

