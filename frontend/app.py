import os
import sys
import streamlit as st

# When deployed as single service, backend runs on localhost:8000
if not os.getenv("API_URL"):
    os.environ["API_URL"] = "http://localhost:8000"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ui_text import ui
from components import sidebar_brand, esc
from auth_helpers import is_staff_session_valid, clear_staff_session

st.set_page_config(
    page_title="JanSamadhan - Multilingual Citizen Grievance Portal",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_css() -> str:
    css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            return f"<style>{f.read()}</style>"
    return ""

st.markdown(load_css(), unsafe_allow_html=True)

if "lang" not in st.session_state:
    st.session_state["lang"] = "en"

lang = st.session_state["lang"]

LANG_OPTIONS = ["English", "हिन्दी", "ଓଡ଼ିଆ", "मराठी"]
LANG_CODE_MAP = {"English": "en", "हिन्दी": "hi", "ଓଡ଼ିଆ": "or", "मराठी": "mr"}
CODE_TO_LANG = {"en": "English", "hi": "हिन्दी", "or": "ଓଡ଼ିଆ", "mr": "मराठी"}

# User & Avatar Info
user = st.session_state.get("user")
user_name = st.session_state.get("citizen_name") or (user.get("name") if (user and isinstance(user, dict) and user.get("id") != "guest") else None) or "Rani"

# Compute Initials
parts = user_name.strip().split()
if len(parts) >= 2:
    initials = f"{parts[0][0]}{parts[1][0]}".upper()
elif len(parts) == 1 and len(parts[0]) >= 2:
    initials = parts[0][:2].upper()
else:
    initials = "RN"

# ── Sidebar Setup ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(sidebar_brand(), unsafe_allow_html=True)

    if is_staff_session_valid():
        st.markdown("<div style='height: 0.25rem;'></div>", unsafe_allow_html=True)
        staff_name = st.session_state.get("staff_name", "Staff")
        role = st.session_state.get("role", "")
        dept = st.session_state.get("department") or "All Departments"
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; padding: 10px; margin-bottom: 8px;">
            <div style="font-size: 13px; font-weight: 700; color: #FFFFFF;">👤 {esc(staff_name)}</div>
            <div style="font-size: 11.5px; color: var(--border);">{esc(role)} • {esc(dept)}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚪 Logout", key="btn_sidebar_logout", use_container_width=True):
            clear_staff_session()
            st.rerun()

    # Clean Digital Public Grievance Portal footer at sidebar bottom (No temples / skylines)
    st.markdown('<div class="sidebar-gov-footer">— Digital Public Grievance Portal —</div>', unsafe_allow_html=True)

# ── Top Bar Header (Main Canvas Top) ─────────────────────────────────────
top_c1, top_c2 = st.columns([3.2, 1.4], vertical_alignment="center")
with top_c1:
    st.markdown(f"""
    <div class="main-topbar-left" style="margin-bottom: 0.75rem;">
        <h2 class="welcome-heading">Welcome, {esc(user_name)}! 👋</h2>
        <p class="welcome-subtitle">Let's resolve your grievances together.</p>
    </div>
    """, unsafe_allow_html=True)

with top_c2:
    tc_lang, tc_avatar = st.columns([2.2, 1], vertical_alignment="center")
    with tc_lang:
        curr_label = CODE_TO_LANG.get(lang, "English")
        sel_label = st.selectbox(
            "Language",
            options=LANG_OPTIONS,
            index=LANG_OPTIONS.index(curr_label),
            key="app_lang_select_topbar",
            label_visibility="collapsed"
        )
        selected_code = LANG_CODE_MAP[sel_label]
        if selected_code != lang:
            st.session_state["lang"] = selected_code
            st.rerun()

    with tc_avatar:
        st.markdown(f"""
        <div class="user-avatar-circle" title="{esc(user_name)}">
            {esc(initials)}
        </div>
        """, unsafe_allow_html=True)

# ── Navigation Pages (Order per prompt) ─────────────────────────────────
views_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "views")
pg_chat = st.Page(os.path.join(views_dir, "chat.py"), title="Chat Assistant", icon="💬", default=True)
pg_complaints = st.Page(os.path.join(views_dir, "complaints.py"), title="My Complaints", icon="📄")
pg_track = st.Page(os.path.join(views_dir, "track.py"), title="Track Status", icon="📋")
pg_notifications = st.Page(os.path.join(views_dir, "notifications.py"), title="Notifications", icon="🔔")
pg_profile = st.Page(os.path.join(views_dir, "profile.py"), title="Profile", icon="👤")
pg_settings = st.Page(os.path.join(views_dir, "settings.py"), title="Settings", icon="⚙️")
pg_help = st.Page(os.path.join(views_dir, "help.py"), title="Help & Support", icon="❓")

citizen_pages = [pg_chat, pg_complaints, pg_track, pg_notifications, pg_profile, pg_settings, pg_help]

if is_staff_session_valid():
    pg_staff = st.Page(os.path.join(views_dir, "staff.py"), title="Staff Portal", icon="🏛️")
    pages = citizen_pages + [pg_staff]
else:
    pages = citizen_pages

nav = st.navigation(pages)

# Demo Banner (shown when in demo mode)
if st.session_state.get("staff_demo") or st.session_state.get("demo_mode"):
    with st.container(key="demo_banner_bar"):
        db_col1, db_col2 = st.columns([5, 1], vertical_alignment="center")
        with db_col1:
            st.markdown(
                '<div class="demo-banner-text"><strong>Demo mode:</strong> you are exploring with sample data</div>',
                unsafe_allow_html=True
            )
        with db_col2:
            if st.button("Exit demo", key="btn_exit_demo", use_container_width=True):
                if st.session_state.get("staff_demo"):
                    clear_staff_session()
                st.session_state.pop("staff_demo", None)
                st.session_state.pop("demo_mode", None)
                st.rerun()

nav.run()
