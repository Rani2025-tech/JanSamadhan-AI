import streamlit as st
from ui_text import ui

def show():
    lang = st.session_state.get("lang", "en")
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <h2 style="margin: 0; font-size: 1.6rem; color: var(--primary);">👤 Citizen Profile</h2>
        <p style="margin: 4px 0 0 0; color: var(--muted); font-size: 14.5px;">Manage your profile and contact details.</p>
    </div>
    """, unsafe_allow_html=True)
    st.info("Profile view is scheduled for Page 5 build.")

if __name__ == "__main__" or "st" in globals():
    show()

