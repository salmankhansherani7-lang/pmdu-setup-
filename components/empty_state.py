"""
Empty-state components and placeholders.
"""
import streamlit as st

def no_data_placeholder(icon: str = "📭", label: str = "No Data Available", message: str = "Upload an Excel or CSV file using the sidebar to view analytics."):
    st.markdown(f"""
    <div style="text-align:center; padding:50px 20px; background:#FFFFFF; border:1px dashed #CBD5E1; border-radius:10px; margin:16px 0;">
        <div style="font-size:42px; margin-bottom:12px;">{icon}</div>
        <div style="font-size:17px; font-weight:700; margin-bottom:6px; color:#1E293B;">{label}</div>
        <div style="font-size:13px; color:#64748B; max-width:460px; margin:0 auto; line-height:1.5;">{message}</div>
    </div>
    """, unsafe_allow_html=True)

def empty_chart_placeholder(title: str = "Chart Analytics"):
    st.markdown(f"""
    <div style="text-align:center; padding:40px 16px; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px; margin-bottom:16px;">
        <div style="font-size:14px; font-weight:700; color:#334155; margin-bottom:12px; text-align:left;">{title}</div>
        <div style="font-size:32px; margin-bottom:8px; opacity:0.6;">📊</div>
        <div style="font-size:13px; color:#94A3B8;">Upload an Excel file to view analytics.</div>
    </div>
    """, unsafe_allow_html=True)
