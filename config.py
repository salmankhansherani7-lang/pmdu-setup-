"""
Configuration and constants for PMDU Complaints Analytics Platform.
"""
import os

# Application Metadata
APP_TITLE = "PMDU Complaints Analytics & Monitoring Platform"
APP_SUBTITLE = "Citizen's Portal Operational Intelligence & Verification System"
APP_VERSION = "2.0.0-Enterprise"

# Color Palette (Clean & Professional Enterprise Theme)
PALETTE = {
    "navy_dark": "#101B33",      # Background base / Dark headers
    "navy_card": "#172A4A",      # Secondary dark cards
    "blue_primary": "#2563EB",   # Primary buttons & highlights
    "blue_light": "#3B82F6",     # Secondary accents
    "teal": "#0F9D91",           # Accents & positive status
    "bg_light": "#F8FAFC",       # Clean light page background
    "card_bg": "#FFFFFF",        # KPI cards & containers
    "card_border": "#E2E8F0",    # Card borders
    "text_primary": "#0F172A",   # Heading & body text
    "text_secondary": "#64748B", # Muted subtitles & labels
    "success": "#10B981",        # Verified totals & passed checks
    "warning": "#F59E0B",        # Warnings / partial matches
    "danger": "#EF4444",         # Errors & discrepancies
    "info": "#2563EB",           # Information notes
}

# Supported standard complaint fields for mapping
STANDARD_FIELDS = {
    "complaint_id": {"label": "Complaint ID / Tracking Code", "required": False, "type": "string"},
    "category": {"label": "Complaint Category / Subject", "required": False, "type": "string"},
    "department": {"label": "Department / Agency", "required": False, "type": "string"},
    "district": {"label": "District", "required": False, "type": "string"},
    "province": {"label": "Province", "required": False, "type": "string"},
    "region": {"label": "Region", "required": False, "type": "string"},
    "status": {"label": "Complaint Status", "required": False, "type": "string"},
    "submission_date": {"label": "Submission Date", "required": False, "type": "date"},
    "resolution_date": {"label": "Resolution Date", "required": False, "type": "date"},
    "count": {"label": "Complaint Count", "required": False, "type": "numeric"},
}

# The 4 canonical PMDU report sections
CANONICAL_SECTIONS = [
    "Forwarded Complaints",
    "Escalated Complaints",
    "Reopened Complaints",
    "Response Awaited Complaints"
]

# Security & Upload Limits
MAX_UPLOAD_SIZE_MB = 50
ALLOWED_EXTENSIONS = [".xlsx", ".xls", ".csv"]

# File Storage Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
REPORTS_DIR = os.path.join(BASE_DIR, "reports", "generated")
DEFAULT_INPUT_FILE = os.path.join(BASE_DIR, "input_data.xlsx")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
