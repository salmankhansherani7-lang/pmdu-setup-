"""
Unit tests for PDF and Excel report generators.
"""
import pytest
import os
import pandas as pd
from reports.pdf_generator import generate_pdf_report
from reports.excel_generator import generate_excel_report
from core.sectional_parser import parse_pmdu_sectional_workbook
from core.calculations import calculate_sectional_metrics
from core.reconciliation import build_sectional_reconciliation_table

def test_pdf_generation_sectional():
    path = "data/reference_templates/20261116 PMDU Complaints Report.xlsx"
    if os.path.exists(path):
        parsed = parse_pmdu_sectional_workbook(path)
        metrics = calculate_sectional_metrics(parsed)
    else:
        metrics = {"sections": {}}
    
    pdf_bytes = generate_pdf_report(metrics, dataset_name="Test Reference Template")
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")

def test_excel_generation_sectional():
    path = "data/reference_templates/20261116 PMDU Complaints Report.xlsx"
    if os.path.exists(path):
        parsed = parse_pmdu_sectional_workbook(path)
        metrics = calculate_sectional_metrics(parsed)
        recon_df = build_sectional_reconciliation_table(parsed)
    else:
        metrics = {"sections": {}}
        recon_df = None
    
    excel_bytes = generate_excel_report(metrics, reconciliation_df=recon_df)
    assert excel_bytes is not None
    assert len(excel_bytes) > 2000
    # PK zip header for xlsx
    assert excel_bytes[:2] == b"PK"

