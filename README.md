# PMDU Complaints Analytics & Monitoring Platform

An enterprise-grade, government-quality analytics and monitoring web application designed for the Prime Minister's Performance Delivery Unit (PMDU) complaint datasets, departmental operational reviews, and executive dashboards.

---

## 🌟 Key Features

1. **Dual Ingestion Architecture**:
   - **Sectional Matrix Format**: Intelligently parses complex matrix layouts (such as the reference `20261116 PMDU Complaints Report.xlsx`), detecting the 4 operational sections (*Forwarded*, *Escalated*, *Reopened*, *Response Awaited*), detail rows, total column merges (`N:O`), and embedded formulas.
   - **Standard Tabular Format**: Supports general CSV and Excel datasets with arbitrary column names, auto-suggesting mappings to standard complaint dimensions (Complaint ID, Category, Department, District, Province, Status, Dates, Count).

2. **Zero-Tolerance Mathematical Verification**:
   - **Original Preservation**: Never alters source files.
   - **Independent Recalculation**: Compares raw detail row sums with Excel cached values and flags any discrepancy.
   - **Strict Missing Values Distinction**: Distinguishes true `0` counts from blank / unpopulated template cells.
   - **Category Integrity Safeguard**: Prevents inappropriate addition of workflow stages without verified mutual exclusivity.
   - **Resolution Rate Safeguard**: Calculates $\text{Resolution Rate} = \left(\frac{\text{Resolved}}{\text{Eligible Total}}\right) \times 100$ only when valid status disposal fields exist.

3. **10 Dedicated Analytical Views**:
   - **Overview**: Executive summary, top KPI cards, section volume distributions, entity aggregations.
   - **Forwarded Complaints**: Detail rows (4–9), entity comparisons, bar charts, and data tables.
   - **Escalated Complaints**: High-priority bottlenecks, supervisory delays, and entity distributions.
   - **Reopened Complaints**: Review grounds, procedural dissatisfaction, and entity breakdowns.
   - **Response Awaited**: Pending departmental compliance and inquiry reports.
   - **Geographical Analysis**: District and provincial breakdowns (active only when valid geographical fields exist).
   - **Trends & Comparisons**: Monthly inflows, trajectory lines, and period-over-period percentage changes.
   - **Master Data Explorer**: Interactive search, column visibility toggle, and filtered CSV export.
   - **Data Quality & Audit Cockpit**: Quality score (0–100), categorization of Errors, Warnings, Passed checks, and complete mathematical reconciliation table.
   - **Reports & Downloads**: On-demand generation of formal **ReportLab PDF documents** and **OpenPyXL multi-sheet Excel workbooks**.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
streamlit run app.py
```
Or directly:
```bash
python main.py
```
Access the application at `http://localhost:8501`.

### 3. Run Automated Unit Tests
```bash
pytest tests/
```

---

## 📁 Project Architecture

```
Dashboard for PMDU/
├── app.py                      # Application entrypoint & navigation router
├── config.py                   # Corporate color palette, limits, schemas
├── requirements.txt            # Dependency specification
├── .gitignore                  # Security rules blocking data leaks
├── data/
│   ├── reference_templates/    # Original untouched PMDU report
│   ├── samples/                # Clearly-labelled synthetic benchmark datasets
│   └── uploads/                # Isolated staging area for user uploads
├── core/
│   ├── format_detector.py      # Autodetects sectional matrix vs tabular
│   ├── excel_reader.py         # OpenPyXL reader for sheets & formulas
│   ├── csv_reader.py           # Robust CSV parser with encoding fallback
│   ├── sectional_parser.py     # PMDU 4-section matrix extractor
│   ├── column_mapping.py       # Column mapping engine & capabilities
│   ├── validation.py           # Zero-tolerance validation engine
│   ├── reconciliation.py       # Formula vs recalculation audit table
│   └── calculations.py         # Verified KPI metrics & aggregations
├── components/
│   ├── navbar.py               # Top header banner with region/date badges
│   ├── sidebar.py              # File uploader, benchmark loader, reset
│   ├── kpi_cards.py            # Custom CSS KPI cards with trace tags
│   ├── charts.py               # Enterprise Plotly charts
│   └── configurators.py       # Sectional label & column mapping UI
├── views/
│   ├── overview.py             # Executive overview
│   ├── forwarded.py            # Forwarded complaints
│   ├── escalated.py            # Escalated complaints
│   ├── reopened.py             # Reopened complaints
│   ├── response_awaited.py     # Response awaited complaints
│   ├── geographical.py         # District / provincial analysis
│   ├── trends.py               # Time trends & period changes
│   ├── data_table.py           # Master search table & CSV export
│   ├── data_quality.py         # Audit cockpit & reconciliation
│   └── reports.py              # PDF & Excel report compiler
├── reports/
│   ├── pdf_generator.py        # ReportLab government-style PDF engine
│   └── excel_generator.py      # OpenPyXL multi-tab styled workbook engine
├── styles/
│   └── custom.css              # Corporate design system styling
└── tests/
    ├── test_readers.py
    ├── test_sectional_parser.py
    ├── test_validation.py
    └── test_reports.py
```

---

## 🔒 Security & Privacy Notice
- Never exposes uploaded private citizen data.
- PII and raw descriptions are excluded from public logging.
- Git excludes uploaded files, database caches, and generated exports.
- Complies with local data isolation standards.

