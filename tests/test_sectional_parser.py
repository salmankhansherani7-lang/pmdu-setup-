"""
Unit tests for PMDU Sectional matrix parser.
"""
import pytest
import os
from core.sectional_parser import parse_pmdu_sectional_workbook, sectional_to_flat_dataframe

def test_parse_reference_template():
    path = "data/reference_templates/20261116 PMDU Complaints Report.xlsx"
    if os.path.exists(path):
        res = parse_pmdu_sectional_workbook(path)
        assert res["success"] is True
        assert "Forwarded Complaints" in res["sections"]
        assert "Escalated Complaints" in res["sections"]
        assert "Reopened Complaints" in res["sections"]
        assert "Response Awaited Complaints" in res["sections"]
        # Detail cells are empty in reference template
        assert res["is_populated"] is False
        assert len(res["column_labels"]) == 11

def test_parse_populated_matrix(tmp_path):
    template_path = "data/reference_templates/20261116 PMDU Complaints Report.xlsx"
    if not os.path.exists(template_path):
        pytest.skip("Reference template not found")
    
    import openpyxl
    wb = openpyxl.load_workbook(template_path)
    ws = wb.active
    # Populate some values in Forwarded Complaints (rows 4 to 9, cols C to M)
    for r in range(4, 10):
        for c in range(3, 14):
            ws.cell(r, c).value = 5
        ws.cell(r, 14).value = 55 # 11 * 5
    
    pop_path = str(tmp_path / "populated_test.xlsx")
    wb.save(pop_path)

    res = parse_pmdu_sectional_workbook(pop_path)
    assert res["success"] is True
    assert res["is_populated"] is True
    fwd = res["sections"]["Forwarded Complaints"]
    assert fwd["grand_total_calculated"] is not None
    assert fwd["grand_total_calculated"] > 0

def test_sectional_flat_dataframe_conversion(tmp_path):
    template_path = "data/reference_templates/20261116 PMDU Complaints Report.xlsx"
    if not os.path.exists(template_path):
        pytest.skip("Reference template not found")

    import openpyxl
    wb = openpyxl.load_workbook(template_path)
    ws = wb.active
    for r in range(4, 10):
        for c in range(3, 14):
            ws.cell(r, c).value = 10

    pop_path = str(tmp_path / "populated_flat.xlsx")
    wb.save(pop_path)

    res = parse_pmdu_sectional_workbook(pop_path)
    df = sectional_to_flat_dataframe(res)
    assert len(df) == 242 # 22 detail rows * 11 columns
    assert "Section" in df.columns
    assert "Complaint_Count" in df.columns

