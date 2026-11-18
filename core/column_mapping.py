"""
Column mapping engine:
Maps arbitrary user CSV/Excel column headers to standard complaint fields.
Only activates analytics supported by the mapped fields.
"""
from typing import Dict, Any, List, Optional
import pandas as pd
from config import STANDARD_FIELDS

def auto_suggest_mappings(columns: List[str]) -> Dict[str, Optional[str]]:
    """
    Intelligently suggests matches between user columns and standard fields.
    Does not force mappings if confidence is low.
    """
    suggestions = {}
    lower_cols = {c: c.lower().strip() for c in columns}

    rules = {
        "complaint_id": ["complaint_id", "complaint id", "complaint_no", "id", "tracking_code", "ticket_id", "ticket_no"],
        "category": ["category", "complaint_category", "subject", "complaint_type", "type", "nature"],
        "department": ["department", "dept", "agency", "ministry", "organization", "office"],
        "district": ["district", "dist", "city", "location"],
        "province": ["province", "prov", "state"],
        "region": ["region", "division", "zone"],
        "status": ["status", "complaint_status", "state", "current_status"],
        "submission_date": ["submission_date", "submitted_date", "created_at", "entry_date", "lodged_date", "date"],
        "resolution_date": ["resolution_date", "resolved_date", "closed_date", "completed_date", "disposal_date"],
        "count": ["count", "complaints_count", "total_complaints", "num_complaints", "frequency", "total"]
    }

    for std_field, candidates in rules.items():
        matched = None
        for col_orig, col_low in lower_cols.items():
            # Exact match
            if col_low in candidates:
                matched = col_orig
                break
            # Substring match
            for cand in candidates:
                if cand in col_low:
                    matched = col_orig
                    break
            if matched:
                break
        suggestions[std_field] = matched

    return suggestions


def apply_column_mapping(df: pd.DataFrame, mapping: Dict[str, Optional[str]]) -> pd.DataFrame:
    """
    Creates a standardized working copy of the DataFrame using mapped columns.
    Original DataFrame is left unchanged.
    """
    mapped_df = pd.DataFrame(index=df.index)
    
    for std_field, source_col in mapping.items():
        if source_col and source_col in df.columns:
            mapped_df[std_field] = df[source_col]
        else:
            mapped_df[std_field] = None

    # Carry over original index and unmapped columns with original names prefixed with 'orig_'
    for col in df.columns:
        if col not in mapping.values():
            mapped_df[f"orig_{col}"] = df[col]

    return mapped_df


def get_supported_capabilities(mapping: Dict[str, Optional[str]]) -> Dict[str, bool]:
    """
    Returns booleans indicating what analytical features the current dataset supports.
    """
    return {
        "has_ids": bool(mapping.get("complaint_id")),
        "has_categories": bool(mapping.get("category")),
        "has_departments": bool(mapping.get("department")),
        "has_districts": bool(mapping.get("district")),
        "has_provinces": bool(mapping.get("province")),
        "has_regions": bool(mapping.get("region")),
        "has_statuses": bool(mapping.get("status")),
        "has_submission_dates": bool(mapping.get("submission_date")),
        "has_resolution_dates": bool(mapping.get("resolution_date")),
        "has_explicit_counts": bool(mapping.get("count")),
    }

