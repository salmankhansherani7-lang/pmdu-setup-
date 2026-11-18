"""
Unit tests for data validation and calculations.
"""
import pytest
import pandas as pd
from core.validation import validate_tabular_dataset, validate_sectional_dataset
from core.calculations import calculate_tabular_metrics, calculate_sectional_metrics
from core.column_mapping import auto_suggest_mappings, apply_column_mapping

def test_validation_clean_tabular():
    df = pd.DataFrame({
        "Complaint_ID": ["C1", "C2", "C3"],
        "Category": ["Health", "Revenue", "Education"],
        "Status": ["Resolved", "Forwarded", "Resolved"],
        "Count": [1, 2, 3]
    })
    mapping = {
        "complaint_id": "Complaint_ID",
        "category": "Category",
        "status": "Status",
        "count": "Count"
    }
    val = validate_tabular_dataset(df, mapping)
    assert val["status"] == "PASSED"
    assert len(val["errors"]) == 0

def test_validation_negative_counts():
    df = pd.DataFrame({
        "Complaint_ID": ["C1", "C2"],
        "Count": [10, -5]
    })
    mapping = {"complaint_id": "Complaint_ID", "count": "Count"}
    val = validate_tabular_dataset(df, mapping)
    assert val["status"] == "FAILED"
    assert any("Negative" in e["check"] for e in val["errors"])

def test_tabular_calculations_resolution_rate():
    df = pd.DataFrame({
        "Complaint_ID": ["C1", "C2", "C3", "C4"],
        "Status": ["Resolved", "Forwarded", "Closed", "Pending"]
    })
    mapping = {"complaint_id": "Complaint_ID", "status": "Status"}
    metrics = calculate_tabular_metrics(df, mapping)
    assert metrics["total_complaints"] == 4
    # Resolved + Closed = 2 -> 50%
    assert metrics["resolution_rate"] == 50.0

def test_tabular_calculations_no_status_field():
    df = pd.DataFrame({
        "Complaint_ID": ["C1", "C2"],
        "Category": ["A", "B"]
    })
    mapping = {"complaint_id": "Complaint_ID", "category": "Category"}
    metrics = calculate_tabular_metrics(df, mapping)
    assert metrics["resolution_rate"] is None
    assert "Not Calculated" in metrics["resolution_rate_note"]

