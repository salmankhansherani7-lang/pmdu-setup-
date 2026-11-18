"""
Validation Engine:
Performs zero-tolerance audit of uploaded data.
Checks missing values, duplicates, invalid dates, negative counts,
unexpected non-numeric data, and formula-cached mismatches.
"""
from typing import Dict, Any, List
import pandas as pd
import numpy as np

def validate_tabular_dataset(df: pd.DataFrame, mapping: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates a standard tabular dataset against mapping and integrity constraints.
    Returns categorized Errors, Warnings, Passed checks, and Quality Score.
    """
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    passed: List[Dict[str, Any]] = []

    total_rows = len(df)
    if total_rows == 0:
        errors.append({
            "check": "Row Count Check",
            "message": "Dataset contains zero rows.",
            "impact": "Cannot perform analytics on empty data."
        })
        return {
            "status": "FAILED",
            "errors": errors,
            "warnings": warnings,
            "passed": passed,
            "quality_score": 0.0,
            "total_rows": 0
        }

    # 1. Missing Values Check
    missing_by_col = df.isnull().sum()
    total_cells = df.size
    total_missing = missing_by_col.sum()
    missing_pct = (total_missing / total_cells * 100) if total_cells > 0 else 0

    if missing_pct > 20.0:
        warnings.append({
            "check": "Missing Values Density",
            "message": f"{missing_pct:.1f}% of total cells are blank/missing across the dataset.",
            "details": missing_by_col[missing_by_col > 0].to_dict()
        })
    else:
        passed.append({
            "check": "Missing Values Density",
            "message": f"Data completeness is acceptable ({100 - missing_pct:.1f}% populated)."
        })

    # Check key mapped columns for nulls
    for field in ["complaint_id", "status", "category"]:
        mapped_col = mapping.get(field)
        if mapped_col and mapped_col in df.columns:
            n_null = df[mapped_col].isnull().sum()
            if n_null > 0:
                warnings.append({
                    "check": f"Missing Values in {field.replace('_', ' ').title()}",
                    "message": f"Found {n_null} missing entries ({n_null/total_rows*100:.1f}%) in mapped column '{mapped_col}'.",
                    "details": {"column": mapped_col, "missing_count": int(n_null)}
                })
            else:
                passed.append({
                    "check": f"Completeness: {field.replace('_', ' ').title()}",
                    "message": f"Column '{mapped_col}' has 100% complete records."
                })

    # 2. Duplicate Records Check
    dup_rows = df.duplicated().sum()
    if dup_rows > 0:
        warnings.append({
            "check": "Duplicate Rows",
            "message": f"Found {dup_rows} identical duplicate rows.",
            "details": {"duplicate_row_count": int(dup_rows)}
        })
    else:
        passed.append({
            "check": "Duplicate Rows Check",
            "message": "No full-row duplicates detected."
        })

    # Complaint ID uniqueness
    id_col = mapping.get("complaint_id")
    if id_col and id_col in df.columns:
        id_series = df[id_col].dropna()
        dup_ids = id_series.duplicated().sum()
        if dup_ids > 0:
            errors.append({
                "check": "Unique Complaint ID Check",
                "message": f"Found {dup_ids} duplicate Complaint IDs in column '{id_col}'.",
                "details": {"duplicate_id_count": int(dup_ids)}
            })
        else:
            passed.append({
                "check": "Unique Complaint ID Check",
                "message": f"All {len(id_series)} Complaint IDs in '{id_col}' are unique."
            })

    # 3. Numeric Integrity & Non-Negative Checks
    count_col = mapping.get("count")
    if count_col and count_col in df.columns:
        # Check non-numeric strings
        non_num = pd.to_numeric(df[count_col], errors="coerce")
        nan_count = non_num.isnull().sum() - df[count_col].isnull().sum()
        if nan_count > 0:
            errors.append({
                "check": "Numeric Format Check",
                "message": f"Found {nan_count} non-numeric values in numeric column '{count_col}'.",
                "details": {"invalid_count": int(nan_count)}
            })
        
        # Check negative counts
        neg_count = (non_num < 0).sum()
        if neg_count > 0:
            errors.append({
                "check": "Negative Value Check",
                "message": f"Found {neg_count} negative complaint counts in '{count_col}'. Counts must be non-negative.",
                "details": {"negative_count": int(neg_count)}
            })
        elif nan_count == 0:
            passed.append({
                "check": "Count Column Integrity",
                "message": f"All values in '{count_col}' are valid non-negative numbers."
            })

    # 4. Date Integrity Checks
    date_cols = [("submission_date", mapping.get("submission_date")), ("resolution_date", mapping.get("resolution_date"))]
    for d_name, col in date_cols:
        if col and col in df.columns:
            parsed_dates = pd.to_datetime(df[col], errors="coerce")
            invalid_dates = parsed_dates.isnull().sum() - df[col].isnull().sum()
            if invalid_dates > 0:
                warnings.append({
                    "check": f"Date Format ({d_name})",
                    "message": f"Found {invalid_dates} unparseable date values in '{col}'.",
                    "details": {"invalid_date_count": int(invalid_dates)}
                })
            else:
                passed.append({
                    "check": f"Date Parsing ({d_name})",
                    "message": f"All non-blank dates in '{col}' are valid."
                })

    # Compute Quality Score (0 to 100)
    # Deduct 25 for each error, 8 for each warning
    score = 100.0 - (len(errors) * 25.0) - (len(warnings) * 8.0)
    score = max(0.0, min(100.0, score))
    status = "PASSED" if len(errors) == 0 else "FAILED"
    if len(errors) == 0 and len(warnings) > 0:
        status = "PASSED_WITH_WARNINGS"

    return {
        "status": status,
        "quality_score": round(score, 1),
        "errors": errors,
        "warnings": warnings,
        "passed": passed,
        "total_rows": total_rows,
        "total_columns": len(df.columns),
        "missing_percentage": round(missing_pct, 2)
    }


def validate_sectional_dataset(sectional_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates a parsed PMDU Sectional matrix report.
    Checks:
    - Section presence (all 4 sections found)
    - Detail rows and columns configuration
    - Population status (are numbers filled or empty template?)
    - Excel formula vs calculated discrepancies
    """
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    passed: List[Dict[str, Any]] = []

    sections = sectional_data.get("sections", {})
    if not sections:
        errors.append({
            "check": "Section Structure Check",
            "message": "No recognized PMDU sections found in worksheet.",
            "impact": "Cannot process matrix layout."
        })
        return {
            "status": "FAILED",
            "quality_score": 0.0,
            "errors": errors,
            "warnings": warnings,
            "passed": passed
        }

    # 1. Check Canonical Sections
    expected_sections = [
        "Forwarded Complaints",
        "Escalated Complaints",
        "Reopened Complaints",
        "Response Awaited Complaints"
    ]
    missing_secs = [s for s in expected_sections if s not in sections]
    if missing_secs:
        warnings.append({
            "check": "Canonical Section Coverage",
            "message": f"Report is missing {len(missing_secs)} standard sections: {', '.join(missing_secs)}.",
            "details": missing_secs
        })
    else:
        passed.append({
            "check": "Canonical Section Coverage",
            "message": "All 4 standard PMDU sections are present in report."
        })

    # 2. Check Data Population
    is_pop = sectional_data.get("is_populated", False)
    if not is_pop:
        warnings.append({
            "check": "Data Population Check",
            "message": "Detail cells in this workbook are unpopulated (empty). Formulas currently evaluate to 0.",
            "details": "This workbook is a blank template. Figures can be configured or a populated dataset can be uploaded."
        })
    else:
        passed.append({
            "check": "Data Population Check",
            "message": "Detail complaint figures are populated."
        })

    # 3. Discrepancy & Reconciliation Audits
    discrepancies = sectional_data.get("discrepancies", [])
    if discrepancies:
        for d in discrepancies:
            errors.append({
                "check": f"Formula Reconciliation ({d['section']})",
                "message": f"Excel cached total ({d['source']}) does not match calculated total ({d['calculated']}). Difference: {d['difference']}",
                "details": d
            })
    else:
        passed.append({
            "check": "Section Formula Reconciliation",
            "message": "All verified section totals agree with independently calculated sums."
        })

    score = 100.0 - (len(errors) * 25.0) - (len(warnings) * 10.0)
    score = max(0.0, min(100.0, score))
    status = "PASSED" if len(errors) == 0 else "FAILED"
    if len(errors) == 0 and len(warnings) > 0:
        status = "PASSED_WITH_WARNINGS"

    return {
        "status": status,
        "quality_score": round(score, 1),
        "errors": errors,
        "warnings": warnings,
        "passed": passed,
        "is_populated": is_pop,
        "total_sections": len(sections),
        "discrepancies": discrepancies
    }

