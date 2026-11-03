import os
import sys
import re
import html
import textwrap
import streamlit as st

# When deployed as single service, backend runs on localhost:8000
if not os.getenv("API_URL"):
    os.environ["API_URL"] = "http://localhost:8000"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ui_text import ui
from icons import icon
from auth_helpers import is_staff_session_valid, clear_staff_session

def clean_html(s: str) -> str:
    if not s:
        return ""
    s = textwrap.dedent(s).strip()
    s = re.sub(r'>\s+<', '><', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

st.set_page_config(
    page_title="JanSamadhan - Grievance Redressal for a Better Odisha",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_css() -> str:
    css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            return f"<style>{f.read()}</style>"
    return ""

st.markdown(load_css(), unsafe_allow_html=True)

# ── Query Params & Language Synchronization ──────────────────────────────
if "lang" in st.query_params:
    qp_l = st.query_params["lang"]
    if qp_l in ["en", "hi", "or", "mr", "te"]:
        st.session_state["lang"] = qp_l

if "lang" not in st.session_state:
    st.session_state["lang"] = "en"

lang = st.session_state["lang"]

LANG_OPTIONS = ["English", "हिन्दी", "ଓଡ଼ିଆ"]
LANG_CODE_MAP = {"English": "en", "हिन्दी": "hi", "ଓଡ଼ିଆ": "or"}
CODE_TO_LANG = {"en": "English", "hi": "हिन्दी", "or": "ଓଡ଼ିଆ"}

# ── User Profile & Dynamic Name Rule ─────────────────────────────────────
# RULE: Never hardcode 'Rani'. Read logged-in user or citizen name.
# If name exists: 'Welcome, <FirstName>! 👋' and 2-letter initials.
# If no name exists: 'Welcome! 👋' and generic white person icon.
user = st.session_state.get("user")
user_name = None
if isinstance(user, dict):
    user_name = user.get("name")
if not user_name:
    user_name = st.session_state.get("citizen_name")

if user_name and str(user_name).strip() and str(user_name).strip().lower() not in ["none", "null"]:
    clean_name = str(user_name).strip()
    first_name = clean_name.split()[0]
    welcome_heading = f"Welcome, {html.escape(first_name)}! 👋"
    parts = clean_name.split()
    if len(parts) >= 2:
        initials = f"{parts[0][0]}{parts[1][0]}".upper()
    else:
        initials = clean_name[:2].upper()
    avatar_html = f'<div class="user-avatar-circle" title="{html.escape(clean_name)}">{html.escape(initials)}</div>'
else:
    welcome_heading = "Welcome! 👋"
    p_svg = icon("user_outline", size=26, color="#FFFFFF")
    avatar_html = f'<div class="user-avatar-circle" title="Citizen">{p_svg}</div>'

# ── Active Page Management ───────────────────────────────────────────────
if "page" in st.query_params:
    st.session_state["nav_page"] = st.query_params["page"]
elif "nav_page" not in st.session_state:
    st.session_state["nav_page"] = "chat"

current_page = st.session_state.get("nav_page", "chat")

# ── Sidebar Setup (Exactly 285px, JanSamadhan Wordmark, 7 Items) ─────────
with st.sidebar:
    # 1. Top Brand Wordmark (No emblem, no logo icon)
    brand_markup = clean_html("""
    <div class="sidebar-brand-box">
        <div class="sidebar-wordmark">JanSamadhan</div>
        <div class="sidebar-tagline">Grievance Redressal<br/>for a Better Odisha</div>
    </div>
    """)
    st.markdown(brand_markup, unsafe_allow_html=True)

    # 2. Nav Items in Exact Order with Outline SVG Icons & Unread Badge
    nav_definitions = [
        ("chat", "Chat Assistant", "chat_bubble_dots", 0),
        ("complaints", "My Complaints", "document_list", 0),
        ("track", "Track Status", "document_list", 0),
        ("notifications", "Notifications", "bell", 2),
        ("profile", "Profile", "user_outline", 0),
        ("settings", "Settings", "settings", 0),
        ("help", "Help & Support", "help_circle", 0),
    ]

    for item_key, label_txt, icon_name, badge_count in nav_definitions:
        is_active = (current_page == item_key)
        active_cls = " active" if is_active else ""
        icon_svg = icon(icon_name, size=26, color="#FFFFFF", stroke_width=1.75)
        badge_html = f'<span class="sidebar-unread-badge">{badge_count}</span>' if badge_count > 0 else ""

        nav_item_html = clean_html(f"""
        <div class="sidebar-nav-item-wrap">
            <a href="?page={item_key}" target="_self" class="sidebar-nav-item{active_cls}" style="color: #FFFFFF !important; text-decoration: none !important;">
                {icon_svg}
                <span class="sidebar-nav-label" style="color: #FFFFFF !important; text-decoration: none !important;">{label_txt}</span>
                {badge_html}
            </a>
        </div>
        """)
        st.markdown(nav_item_html, unsafe_allow_html=True)

    # Staff portal link if staff session active
    if is_staff_session_valid():
        staff_name = st.session_state.get("staff_name", "Staff")
        role = st.session_state.get("role", "")
        dept = st.session_state.get("department") or "All Departments"
        st_markup = clean_html(f"""
        <div style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); border-radius: 12px; padding: 10px; margin: 10px 0;">
            <div style="font-size: 13px; font-weight: 700; color: #FFFFFF;">👤 {html.escape(staff_name)}</div>
            <div style="font-size: 11.5px; color: rgba(255,255,255,0.7);">{html.escape(role)} • {html.escape(dept)}</div>
        </div>
        """)
        st.markdown(st_markup, unsafe_allow_html=True)
        if st.button("🚪 Logout Staff", key="btn_sidebar_logout", use_container_width=True):
            clear_staff_session()
            st.rerun()

    # 3. Sidebar Footer: Centered "Government of Odisha" with thin lines
    footer_markup = clean_html("""
    <div class="sidebar-footer-box">
        <div class="sidebar-footer-line"></div>
        <span class="sidebar-footer-text">— Government of Odisha —</span>
        <div class="sidebar-footer-line"></div>
    </div>
    """)
    st.markdown(footer_markup, unsafe_allow_html=True)

# ── Top Bar Header (Height ~118px, Welcome Left, Language & 52px Avatar Right)
top_c1, top_c2 = st.columns([3.2, 1.4], vertical_alignment="center")
with top_c1:
    topbar_left_html = clean_html(f"""
    <div class="topbar-left" style="margin-bottom: 0.5rem;">
        <h2 class="topbar-welcome">{welcome_heading}</h2>
        <p class="topbar-subtitle">Let's resolve your grievances together.</p>
    </div>
    """)
    st.markdown(topbar_left_html, unsafe_allow_html=True)

with top_c2:
    tc_lang, tc_div, tc_avatar = st.columns([2.4, 0.2, 1], vertical_alignment="center")
    with tc_lang:
        curr_label = CODE_TO_LANG.get(lang, "English")
        sel_label = st.selectbox(
            "Language",
            options=LANG_OPTIONS,
            index=LANG_OPTIONS.index(curr_label) if curr_label in LANG_OPTIONS else 0,
            key="app_lang_select_topbar",
            label_visibility="collapsed"
        )
        selected_code = LANG_CODE_MAP[sel_label]
        if selected_code != lang:
            st.session_state["lang"] = selected_code
            st.query_params["lang"] = selected_code
            st.rerun()

    with tc_div:
        st.markdown('<div class="topbar-divider"></div>', unsafe_allow_html=True)

    with tc_avatar:
        st.markdown(avatar_html, unsafe_allow_html=True)

# ── Active View Dispatcher ───────────────────────────────────────────────
if current_page == "chat":
    import views.chat as chat_view
    chat_view.show()
elif current_page == "complaints":
    import views.complaints as complaints_view
    complaints_view.show()
elif current_page == "track":
    import views.track as track_view
    track_view.show()
elif current_page == "notifications":
    import views.notifications as notifications_view
    notifications_view.show()
elif current_page == "profile":
    import views.profile as profile_view
    profile_view.show()
elif current_page == "settings":
    import views.settings as settings_view
    settings_view.show()
elif current_page == "help":
    import views.help as help_view
    help_view.show()
elif current_page == "staff":
    import views.staff as staff_view
    staff_view.show()
else:
    import views.chat as chat_view
    chat_view.show()
