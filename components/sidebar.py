"""
PMDU Complaints Analytics & Monitoring Platform — Sidebar Component.
Clean, navigation-focused sidebar with dynamic file upload.
No sample, demo, or fake data.
"""
import streamlit as st
import os
from config import BASE_DIR, DEFAULT_INPUT_FILE

NAV_ITEMS = [
    {"label": "Overview", "icon": "📊"},
    {"label": "Forwarded Complaints", "icon": "📨"},
    {"label": "Escalated Complaints", "icon": "⚠️"},
    {"label": "Reopened Complaints", "icon": "🔄"},
    {"label": "Response Awaited", "icon": "⏳"},
    {"label": "Data Quality", "icon": "🛡️"},
    {"label": "Data Table", "icon": "🔍"},
    {"label": "Geographic Analysis", "icon": "🗺️"},
    {"label": "Trends", "icon": "📈"},
    {"label": "Reports", "icon": "📥"},
]

def render_sidebar():
    """
    Renders the sidebar with:
    - App branding
    - Navigation menu with all 10 verified sections
    - File upload widget (xlsx, xls, csv)
    - Active file information card
    - Reset / clear button
    """
    with st.sidebar:
        # ── App Branding ─────────────────────────────────────────────
        st.markdown("""
        <div style="padding-bottom:14px; margin-bottom:16px; border-bottom:1px solid #E2E8F0;">
            <div style="font-size:19px; font-weight:800; color:#0F172A; display:flex; align-items:center; gap:8px;">
                <span>🏛️</span> PMDU Analytics
            </div>
            <div style="font-size:12px; color:#64748B; margin-top:2px;">Complaints Monitoring Platform</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Navigation Menu ──────────────────────────────────────────
        st.markdown("<p style='font-size:11px; font-weight:700; text-transform:uppercase; color:#64748B; letter-spacing:0.05em; margin-bottom:8px;'>Navigation</p>", unsafe_allow_html=True)

        # Default active page
        if "active_page" not in st.session_state:
            st.session_state["active_page"] = "Overview"

        for item in NAV_ITEMS:
            lbl = item["label"]
            icon = item["icon"]
            display_text = f"{icon}  {lbl}"
            is_active = (st.session_state["active_page"] == lbl)
            btn_type = "primary" if is_active else "secondary"

            if st.button(display_text, key=f"nav_btn_{lbl}", use_container_width=True, type=btn_type):
                st.session_state["active_page"] = lbl
                st.rerun()

        st.markdown("<div style='margin-top:16px; margin-bottom:16px; border-top:1px solid #E2E8F0;'></div>", unsafe_allow_html=True)

        # ── Dynamic File Upload ──────────────────────────────────────
        st.markdown("<p style='font-size:11px; font-weight:700; text-transform:uppercase; color:#64748B; letter-spacing:0.05em; margin-bottom:4px;'>Data Source</p>", unsafe_allow_html=True)
        st.caption("Upload your complaint Excel (.xlsx/.xls) or CSV file. All calculations update dynamically.")

        uploaded_file = st.file_uploader(
            label="Upload Data File",
            type=["xlsx", "xls", "csv"],
            help="Upload your PMDU Complaints Report (.xlsx) or tabular complaint dataset.",
            label_visibility="collapsed"
        )

        if uploaded_file is not None:
            new_key = f"{uploaded_file.name}_{uploaded_file.size}"
            if st.session_state.get("_file_key") != new_key:
                file_bytes = uploaded_file.read()
                st.session_state["raw_uploaded_file"] = file_bytes
                st.session_state["current_uploaded_filename"] = uploaded_file.name
                st.session_state["dataset_source_label"] = uploaded_file.name
                st.session_state["_file_key"] = new_key
                # Clear stale cached analyses / mappings from previous file
                for k in ["user_column_mapping", "configured_sectional_cols",
                          "configured_sectional_rows", "cached_pdf_bytes",
                          "cached_excel_bytes"]:
                    st.session_state.pop(k, None)
                st.rerun()

        # Check if local input_data.xlsx exists in project root as an alternative
        if os.path.exists(DEFAULT_INPUT_FILE) and st.session_state.get("current_uploaded_filename") != "input_data.xlsx":
            if st.button("📁 Load local input_data.xlsx", use_container_width=True):
                with open(DEFAULT_INPUT_FILE, "rb") as f:
                    file_bytes = f.read()
                st.session_state["raw_uploaded_file"] = file_bytes
                st.session_state["current_uploaded_filename"] = "input_data.xlsx"
                st.session_state["dataset_source_label"] = "input_data.xlsx"
                st.session_state["_file_key"] = f"input_data.xlsx_{len(file_bytes)}"
                for k in ["user_column_mapping", "configured_sectional_cols",
                          "configured_sectional_rows", "cached_pdf_bytes",
                          "cached_excel_bytes"]:
                    st.session_state.pop(k, None)
                st.rerun()

        st.markdown("<div style='margin-top:14px; margin-bottom:14px; border-top:1px solid #E2E8F0;'></div>", unsafe_allow_html=True)

        # ── Active File Card / Empty Indicator ───────────────────────
        active_name = st.session_state.get("dataset_source_label")
        if active_name:
            st.markdown(f"""
            <div style="background:#F1F5F9; border-radius:8px; padding:12px;
                        border:1px solid #E2E8F0; margin-bottom:12px;">
                <div style="font-size:10px; font-weight:700; color:#64748B;
                            text-transform:uppercase; letter-spacing:0.04em;">Active Source File</div>
                <div style="font-size:13px; font-weight:700; color:#0F172A;
                            word-break:break-all; margin-top:2px;">📄 {active_name}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🗑️ Remove File & Reset", use_container_width=True):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.session_state["_user_cleared"] = True
                st.rerun()
        else:
            st.markdown("""
            <div style="background:#FFF7ED; border-radius:8px; padding:12px;
                        border:1px solid #FED7AA; margin-bottom:10px;">
                <div style="font-size:12px; color:#C2410C; font-weight:700;">
                    ⚠️ No File Loaded
                </div>
                <div style="font-size:11px; color:#9A3412; margin-top:3px; line-height:1.4;">
                    Upload an Excel or CSV file to activate dashboard analytics.
                </div>
            </div>
            """, unsafe_allow_html=True)
