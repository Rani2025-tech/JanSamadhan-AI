import os
import streamlit as st

from ui_text import ui, supported_languages
import api_client
from auth_helpers import (
    is_staff_session_valid,
    set_staff_session,
    clear_staff_session,
    valid_mobile
)
from components import esc
from icons import icon

def show():
    # ── Page-Scoped CSS (Fullscreen Background & Viewport Fit) ───────────
    st.markdown("""
    <style>
        header[data-testid="stHeader"],
        [data-testid="stHeader"] {
            display: none !important;
            background: transparent !important;
        }
        [data-testid="stToolbar"] { display: none !important; }
        footer { display: none !important; }
        section[data-testid="stSidebar"],
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarNavCollapseButton"] {
            display: none !important;
        }
        .app-header-bar {
            display: none !important;
        }
        [data-testid="stApp"],
        .stApp {
            background: linear-gradient(90deg, var(--scrim-strong) 0%, var(--scrim-soft) 42%, rgba(0, 0, 0, 0) 66%),
                        url("/app/static/login_bg.jpg") var(--bg-pos) / cover no-repeat fixed,
                        linear-gradient(180deg, var(--hero-from), var(--hero-to)) !important;
        }
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"],
        .main,
        .block-container {
            background: transparent !important;
            background-color: transparent !important;
            padding: 0 !important;
            max-width: none !important;
        }
        @media (min-height: 520px) and (min-width: 1001px) {
            html, body,
            [data-testid="stApp"],
            [data-testid="stAppViewContainer"],
            [data-testid="stMain"] {
                height: 100vh !important;
                height: 100dvh !important;
                overflow: hidden !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    if "lang" not in st.session_state:
        st.session_state["lang"] = "en"
    lang = st.session_state["lang"]

    if "role" in st.query_params:
        qp_role = st.query_params.get("role", "").lower().strip()
        if qp_role in ("citizen", "official", "admin"):
            st.session_state["login_role"] = qp_role
            st.query_params.clear()

    if "login_role" not in st.session_state:
        st.session_state["login_role"] = "citizen"
    login_role = st.session_state["login_role"]

    LANG_LIST = [(item["code"], item.get("native") or item.get("name")) for item in supported_languages()]

    # Check if logo exists in static
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
    logo_exists = os.path.exists(os.path.join(static_dir, "logo.png"))

    # ── Two-Column Layout [1.1, 1] Centered ──────────────────────────────
    with st.container(key="hero_section"):
        col_left, col_right = st.columns([1.1, 1], gap="medium", vertical_alignment="center")

        # ── LEFT COLUMN ──────────────────────────────────────────────────
        with col_left:
            with st.container(key="landing_left"):
                if logo_exists:
                    st.markdown(
                        '<img src="/app/static/logo.png" alt="JanSamadhan" class="landing-logo" />',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        '<div class="landing-wordmark">JanSamadhan</div>',
                        unsafe_allow_html=True
                    )

                st.markdown(
                    f'<h1 class="landing-headline">{ui("landing_headline", lang)}</h1>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    f'<div class="landing-tagline">{esc(ui("landing_tagline", lang))}</div>',
                    unsafe_allow_html=True
                )

                # Language Selection Pills (direct st.button elements, CSS flex-wraps them)
                with st.container(key="lang_chips"):
                    for code, lbl in LANG_LIST:
                        btn_type = "primary" if lang == code else "secondary"
                        if st.button(lbl, key=f"btn_lang_chip_{code}", type=btn_type):
                            st.session_state["lang"] = code
                            st.rerun()

                st.markdown(
                    f'<div class="landing-proto-note">{esc(ui("demo_prototype", lang))}</div>',
                    unsafe_allow_html=True
                )

        # ── RIGHT COLUMN: LOGIN CONTAINER & CARD ────────────────────────
        with col_right:
            with st.container(key="landing_right"):
                with st.container(key="login_card"):
                    # Header: Left-aligned with LockKeyhole icon
                    st.markdown(f"""
                    <div class="login-card-header-v2">
                        <div class="login-header-icon">
                            {icon("lock_keyhole", size=32, color="var(--primary-dark)", stroke_width=2.5)}
                        </div>
                        <div class="login-header-text">
                            <h2 class="login-header-title">Login to<br/>JanSamadhan</h2>
                            <div class="login-header-subtitle">{esc(ui("login_card_subtitle", lang))}</div>
                        </div>
                    </div>
                    <div class="login-header-divider"></div>
                    """, unsafe_allow_html=True)

                    # Three Role Cards (Dedicated Grid Container)
                    is_c = (login_role == "citizen")
                    is_o = (login_role == "official")
                    is_a = (login_role == "admin")

                    c_cls = "role-card selected" if is_c else "role-card"
                    o_cls = "role-card selected" if is_o else "role-card"
                    a_cls = "role-card selected" if is_a else "role-card"

                    c_color = "#FFFFFF" if is_c else "var(--primary-dark)"
                    o_color = "#FFFFFF" if is_o else "var(--primary-dark)"
                    a_color = "#FFFFFF" if is_a else "var(--primary-dark)"

                    c_label = esc(ui("role_citizen", lang))
                    o_label = esc(ui("role_official", lang)).replace(" ", "<br/>")
                    a_label = esc(ui("role_admin", lang))

                    st.markdown(f"""
                    <div class="role-selection-container">
                        <a href="?role=citizen" target="_self" class="{c_cls}">
                            <div class="role-card-icon">{icon("users", size=24, color=c_color, stroke_width=2.0)}</div>
                            <div class="role-card-label">{c_label}</div>
                        </a>
                        <a href="?role=official" target="_self" class="{o_cls}">
                            <div class="role-card-icon">{icon("landmark", size=24, color=o_color, stroke_width=2.0)}</div>
                            <div class="role-card-label">{o_label}</div>
                        </a>
                        <a href="?role=admin" target="_self" class="{a_cls}">
                            <div class="role-card-icon">{icon("shield_check", size=24, color=a_color, stroke_width=2.0)}</div>
                            <div class="role-card-label">{a_label}</div>
                        </a>
                    </div>
                    """, unsafe_allow_html=True)

                    demo_mode_on = (os.getenv("DEMO_MODE", "0").strip() == "1")

                    if login_role == "citizen":
                        # ── Citizen Flow ─────────────────────────────────
                        st.markdown(f"""
                        <div class="mobile-section">
                            <div class="field-label-bold">{esc(ui("label_mobile", lang))}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        c_mobile = st.text_input(
                            ui("label_mobile", lang),
                            value=st.session_state.get("contact", ""),
                            placeholder=ui("ph_mobile", lang),
                            key="login_mobile",
                            label_visibility="collapsed"
                        )

                        if c_mobile:
                            norm_num = valid_mobile(c_mobile)
                            if norm_num:
                                st.session_state["contact"] = norm_num
                            else:
                                st.caption(ui("invalid_mobile_msg", lang))
                        else:
                            st.session_state.pop("contact", None)

                        btn_label = ui("btn_send_otp", lang)
                        if st.button(btn_label, key="btn_home_start_chat", type="primary", use_container_width=True):
                            st.switch_page("views/chat.py")

                        st.markdown(f"""
                        <div class="or-divider">
                            <div class="divider-line"></div>
                            <span>{esc(ui("or_text", lang))}</span>
                            <div class="divider-line"></div>
                        </div>
                        """, unsafe_allow_html=True)

                        if demo_mode_on:
                            if st.button(ui("btn_demo_citizen", lang), key="btn_demo_citizen", use_container_width=True):
                                st.session_state["demo_mode"] = "citizen"
                                st.switch_page("views/chat.py")

                        if st.button(ui("link_have_account_login", lang), key="btn_home_switch_login", use_container_width=True):
                            st.session_state["login_role"] = "official"
                            st.rerun()

                        # Privacy Box (Citizen)
                        st.markdown(f"""
                        <div class="login-privacy-box">
                            <div class="login-privacy-icon">
                                {icon("shield_check", size=28, color="var(--primary-dark)", stroke_width=2.0)}
                            </div>
                            <div class="login-privacy-text">
                                <div class="login-privacy-title">{esc(ui("privacy_safe_title", lang))}</div>
                                <div class="login-privacy-sub">{esc(ui("privacy_safe_sub", lang))}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    else:
                        # ── Official & Admin Flow ────────────────────────
                        if is_staff_session_valid():
                            s_name = st.session_state.get("staff_name", "Staff")
                            s_role = st.session_state.get("role", "")
                            s_dept = st.session_state.get("department") or "All Departments"
                            st.markdown(f"""
                            <div class="signed-in-panel">
                                <div class="signed-in-name">Signed in as {esc(s_name)} ({esc(s_role)})</div>
                                <div class="signed-in-dept">{esc(s_dept)}</div>
                            </div>
                            """, unsafe_allow_html=True)

                            sc1, sc2 = st.columns(2)
                            with sc1:
                                if st.button("Open staff portal", key="btn_home_portal_open", type="primary", use_container_width=True):
                                    st.switch_page("views/staff.py")
                            with sc2:
                                if st.button("Logout", key="btn_home_portal_logout", use_container_width=True):
                                    clear_staff_session()
                                    st.rerun()
                        else:
                            with st.form(key=f"home_form_staff_auth_{login_role}"):
                                st.markdown(f'<div class="field-label-bold">{esc(ui("label_email", lang))}</div>', unsafe_allow_html=True)
                                staff_email = st.text_input(
                                    ui("label_email", lang),
                                    placeholder=ui("ph_email", lang),
                                    key="login_email",
                                    label_visibility="collapsed"
                                )
                                st.markdown(f'<div class="field-label-bold">{esc(ui("label_password", lang))}</div>', unsafe_allow_html=True)
                                staff_pass = st.text_input(
                                    ui("label_password", lang),
                                    type="password",
                                    placeholder=ui("ph_password", lang),
                                    key="login_password",
                                    label_visibility="collapsed"
                                )
                                btn_staff_sub = st.form_submit_button(
                                    ui("login_button", lang),
                                    type="primary",
                                    use_container_width=True
                                )

                            if btn_staff_sub:
                                if not staff_email or not staff_pass:
                                    st.warning(ui("warn_email_password", lang))
                                else:
                                    try:
                                        login_res = api_client.login(staff_email, staff_pass)
                                        returned_role = login_res.get("role")
                                        if not role_allowed(login_role, returned_role):
                                            st.error(ui("err_role_mismatch", lang) or "This account cannot log in here")
                                        else:
                                            set_staff_session(login_res)
                                            st.success(ui("auth_success", lang))
                                            st.switch_page("views/staff.py")
                                    except api_client.ApiError as err:
                                        st.error(err.message)
                                    except Exception as e:
                                        st.error(f"Login failed: {e}")

                            st.markdown(f"""
                            <div class="or-divider">
                                <div class="divider-line"></div>
                                <span>{esc(ui("or_text", lang))}</span>
                                <div class="divider-line"></div>
                            </div>
                            """, unsafe_allow_html=True)

                            if demo_mode_on:
                                demo_key = "btn_demo_admin" if login_role == "admin" else "btn_demo_official"
                                demo_label = ui("btn_demo_admin", lang) if login_role == "admin" else ui("btn_demo_official", lang)
                                if st.button(demo_label, key=demo_key, use_container_width=True):
                                    try:
                                        with st.spinner("Logging into demo session..."):
                                            login_res = api_client.demo_login(login_role)
                                            set_staff_session(login_res)
                                            st.switch_page("views/staff.py")
                                    except api_client.ApiError as err:
                                        st.error(err.message)
                                    except Exception as e:
                                        st.error(f"Demo login failed: {e}")

                            if st.button(ui("link_back_citizen", lang), key="btn_home_switch_citizen", use_container_width=True):
                                st.session_state["login_role"] = "citizen"
                                st.rerun()

                            st.markdown(f'<div class="staff-admin-note">{esc(ui("staff_admin_created_note", lang))}</div>', unsafe_allow_html=True)

                        # Privacy Box (Staff / Admin)
                        st.markdown(f"""
                        <div class="login-privacy-box">
                            <div class="login-privacy-icon">
                                {icon("shield_check", size=28, color="var(--primary-dark)", stroke_width=2.0)}
                            </div>
                            <div class="login-privacy-text">
                                <div class="login-privacy-title">{esc(ui("privacy_staff_title", lang))}</div>
                                <div class="login-privacy-sub">{esc(ui("privacy_staff_sub", lang))}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

if __name__ == "__main__" or "st" in globals():
    show()
