"""
Unit tests for Excel and CSV reader engines.
"""
import pytest
import os
import pandas as pd
from core.csv_reader import read_csv_safe
from core.excel_reader import get_excel_sheets, read_excel_tabular
from core.format_detector import detect_file_format

def test_detect_format_sectional():
    path = "data/reference_templates/20261116 PMDU Complaints Report.xlsx"
    if os.path.exists(path):
        res = detect_file_format(path)
        assert res["format"] == "pmdu_sectional"
        assert "Forwarded Complaints".lower() in [s.lower() for s in res["detected_sections"]]

def test_detect_format_csv(tmp_path):
    csv_file = tmp_path / "test_complaints.csv"
    csv_file.write_text("Complaint_ID,Category,Status,Submission_Date\nC1,Health,Resolved,2026-01-01\nC2,Education,Pending,2026-01-02\n")
    res = detect_file_format(str(csv_file))
    assert res["format"] == "standard_tabular"

def test_csv_reader_safe(tmp_path):
    csv_file = tmp_path / "test_complaints.csv"
    csv_file.write_text("Complaint_ID,Category,Status,Submission_Date\nC1,Health,Resolved,2026-01-01\nC2,Education,Pending,2026-01-02\n")
    res = read_csv_safe(str(csv_file))
    assert res["success"] is True
    assert res["total_rows"] == 2
    assert "Complaint_ID" in res["columns"]
    assert "Status" in res["columns"]

def test_excel_sheet_list():
    path = "data/reference_templates/20261116 PMDU Complaints Report.xlsx"
    if os.path.exists(path):
        sheets = get_excel_sheets(path)
        assert len(sheets) >= 1
        assert "20261116 0800" in sheets

