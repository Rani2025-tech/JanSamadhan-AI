"""
JanSamadhan - Page 1: Chat Assistant
Multilingual Conversational Grievance Intake & Real-Time Tracking.
Matches the official visual design reference (purple-and-white theme, 
dual-column layout, understanding card, status stepper, and quick action tiles).
"""

import os
import streamlit as st
from datetime import datetime
from html import escape as esc

import api_client
from ui_text import ui, label, supported_languages
from icons import icon
from components import (
    normalize_ticket_id,
    pin_notice,
    status_pill,
    priority_chip,
    build_receipt
)

def _format_time(dt_val=None) -> str:
    """Formats current or provided timestamp to HH:MM AM/PM."""
    if not dt_val:
        return datetime.now().strftime("%I:%M %p")
    try:
        if isinstance(dt_val, str):
            # Parse ISO or YYYY-MM-DD HH:MM:SS
            clean_str = dt_val.replace("T", " ")[:19]
            dt = datetime.strptime(clean_str, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%I:%M %p")
    except Exception:
        pass
    return str(dt_val)[:16]

def _render_understanding_card(meta: dict, lang: str = "en") -> str:
    """Renders 3-column Category / Location / Summary card matching the reference design."""
    tid = esc(meta.get("ticket_id", "GRV-1042"))
    cat_val = meta.get("category") or "Water Supply"
    cat = esc(label("categories", cat_val, lang) if cat_val else cat_val)
    loc = esc(meta.get("location") or meta.get("area") or "Berhampur, Ganjam")
    summary = esc(meta.get("summary") or "Water supply not coming for 2 days")
    dept_val = meta.get("department", "Water Resources Department")
    dept = esc(label("departments", dept_val, lang))
    conf_val = meta.get("confidence")
    conf_pct = round(float(conf_val if conf_val is not None else 0.95) * 100)

    return f"""
    <div class="understanding-summary-box">
        <div class="understanding-col">
            <span class="u-icon">💧</span>
            <div>
                <div class="u-label">{esc(ui('category', lang))}</div>
                <div class="u-value">{cat}</div>
            </div>
        </div>
        <div class="understanding-col">
            <span class="u-icon">📍</span>
            <div>
                <div class="u-label">{esc(ui('location', lang))}</div>
                <div class="u-value">{loc}</div>
            </div>
        </div>
        <div class="understanding-col">
            <span class="u-icon">📄</span>
            <div>
                <div class="u-label">{esc(ui('summary_title', lang))}</div>
                <div class="u-value">{summary}</div>
            </div>
        </div>
    </div>
    <div style="font-size: 13.5px; color: var(--text); margin: 6px 0 8px 0; line-height: 1.4;">
        I will forward this to the <strong>{dept}</strong> with confidence score of <strong>{conf_pct}%</strong>.
    </div>
    <div style="font-size: 13.5px; color: var(--text); margin-bottom: 4px;">
        Your Tracking ID is: <span class="tracking-pill-badge">{tid}</span>
    </div>
    """

def _render_stepper_card(status: str = "Assigned", history: list = None, lang: str = "en") -> str:
    """Renders Complaint Status stepper matching the visual progress line in the screenshot."""
    steps = ["Submitted", "Assigned", "In Progress", "Resolved"]
    stat_clean = (status or "Assigned").strip()
    
    if stat_clean.lower() == "resolved":
        curr_idx = 3
    elif stat_clean.lower() in ["in progress", "reopened"]:
        curr_idx = 2
    elif stat_clean.lower() == "assigned":
        curr_idx = 1
    else:
        curr_idx = 0

    times = {
        "Submitted": "10:24 AM",
        "Assigned": "11:10 AM" if curr_idx >= 1 else ""
    }
    if history and isinstance(history, list):
        for h in history:
            s_name = h.get("status")
            t_raw = h.get("created_at")
            if s_name and t_raw:
                times[s_name] = _format_time(t_raw)

    items_html = []
    for idx, s_name in enumerate(steps):
        if idx < curr_idx:
            c_cls = "done"
            inner = "✓"
        elif idx == curr_idx:
            c_cls = "active"
            inner = ""
        else:
            c_cls = "pending"
            inner = "⚙️" if s_name == "In Progress" else "✓"

        t_str = times.get(s_name, "")
        t_html = f'<div class="stepper-node-timestamp">({t_str})</div>' if t_str else ''

        items_html.append(f"""
        <div class="stepper-node-item">
            <div class="stepper-node-circle {c_cls}">{inner}</div>
            <div class="stepper-node-name">{esc(label('statuses', s_name, lang))}</div>
            {t_html}
        </div>
        """)

    return f"""
    <div class="stepper-progress-box">
        <div class="stepper-progress-header">Complaint Status</div>
        <div class="stepper-nodes-row">
            {"".join(items_html)}
        </div>
    </div>
    """

def show():
    if "lang" not in st.session_state:
        st.session_state["lang"] = "en"
    lang = st.session_state["lang"]

    if "messages" not in st.session_state:
        # Default sample conversation matching the screenshot for instant demo excellence
        st.session_state["messages"] = [
            {
                "role": "user",
                "content": "Water supply problem in Berhampur",
                "time": "10:24 AM"
            },
            {
                "role": "assistant",
                "content": "I've understood your complaint!",
                "time": "10:24 AM",
                "meta": {
                    "ticket_id": "GRV-1042",
                    "category": "Water Supply",
                    "department": "Water Resources Department",
                    "location": "Berhampur, Ganjam",
                    "summary": "Water supply not coming for 2 days",
                    "confidence": 0.95,
                    "priority": "High"
                },
                "status": "Assigned"
            },
            {
                "role": "user",
                "content": "What is the current status of GRV-1042?",
                "time": "10:45 AM"
            },
            {
                "role": "assistant",
                "content": (
                    "Here's the latest update for your complaint:<br/>"
                    "<strong>Status: <span style='color: var(--primary);'>Assigned</span></strong><br/>"
                    "<strong>Assigned To:</strong> Water Resources Department<br/>"
                    "<strong>Last Updated:</strong> 11:10 AM, 28 Oct 2026<br/><br/>"
                    "You'll be notified once the action is taken."
                ),
                "time": "10:45 AM"
            }
        ]

    if "chat_state" not in st.session_state:
        st.session_state["chat_state"] = {"stage": "idle", "pending": {}, "lang": lang}
    if "track_id" not in st.session_state:
        st.session_state["track_id"] = "GRV-1042"
    if "last_meta" not in st.session_state:
        st.session_state["last_meta"] = {
            "ticket_id": "GRV-1042",
            "category": "Water Supply",
            "location": "Berhampur, Ganjam",
            "summary": "Water supply not coming for 2 days",
            "submitted_on": "28 Oct 2026, 10:24 AM",
            "status": "Assigned"
        }

    # Process quick-reply prompt if triggered
    pending_prompt = st.session_state.pop("pending_input", None)

    col_chat, col_side = st.columns([2.1, 1], gap="medium")

    # =========================================================================
    # LEFT COLUMN: Interactive Chat Card
    # =========================================================================
    with col_chat:
        st.markdown("""
        <div class="chat-assistant-container">
        """, unsafe_allow_html=True)

        # ── Card Header (Bot avatar + Status + Language Chips) ───────────
        ch_c1, ch_c2 = st.columns([1.8, 1.2], vertical_alignment="center")
        with ch_c1:
            st.markdown(f"""
            <div class="assistant-info-group">
                <div class="assistant-avatar-badge">
                    {icon("bot", size=24, color="var(--primary)")}
                </div>
                <div>
                    <div class="assistant-title-text">JanSamadhan Assistant</div>
                    <div class="assistant-status-row">
                        <span class="online-dot"></span>
                        <span>Online</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with ch_c2:
            st.markdown('<div class="multilingual-chips-group">', unsafe_allow_html=True)
            sc1, sc2, sc3, sc4, sc5 = st.columns([1.1, 1, 1, 1, 1], vertical_alignment="center")
            with sc1:
                st.markdown('<div class="multilingual-chips-label">Multilingual:</div>', unsafe_allow_html=True)
            with sc2:
                btn_en = "primary" if lang == "en" else "secondary"
                if st.button("English", key="chip_top_en", type=btn_en, use_container_width=True):
                    st.session_state["lang"] = "en"
                    st.rerun()
            with sc3:
                btn_hi = "primary" if lang == "hi" else "secondary"
                if st.button("हिंदी", key="chip_top_hi", type=btn_hi, use_container_width=True):
                    st.session_state["lang"] = "hi"
                    st.rerun()
            with sc4:
                btn_or = "primary" if lang == "or" else "secondary"
                if st.button("ଓଡ଼ିଆ", key="chip_top_or", type=btn_or, use_container_width=True):
                    st.session_state["lang"] = "or"
                    st.rerun()
            with sc5:
                btn_mr = "primary" if lang == "mr" else "secondary"
                if st.button("मराठी", key="chip_top_mr", type=btn_mr, use_container_width=True):
                    st.session_state["lang"] = "mr"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<hr style='border: none; border-top: 1px solid var(--border); margin: 8px 0 14px 0;'/>", unsafe_allow_html=True)

        # ── Message Stream Container ─────────────────────────────────────
        for msg in st.session_state["messages"]:
            role = msg.get("role", "assistant")
            content = msg.get("content", "")
            m_time = msg.get("time") or _format_time()
            meta = msg.get("meta") or {}

            if role == "user":
                st.markdown(f"""
                <div class="chat-bubble-row user-row">
                    <div class="bubble-user-content">
                        {esc(content)}
                        <div class="msg-meta-footer">
                            <span>{esc(m_time)}</span>
                            <span style="color: var(--primary); font-weight: 700; margin-left: 2px;">✓✓</span>
                        </div>
                    </div>
                    <div class="chat-avatar-mini user">
                        {icon("user", size=18, color="#FFFFFF")}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                understanding_html = ""
                stepper_html = ""
                if meta and meta.get("ticket_id"):
                    understanding_html = _render_understanding_card(meta, lang)
                    stepper_html = _render_stepper_card(msg.get("status", "Assigned"), lang=lang)

                st.markdown(f"""
                <div class="chat-bubble-row bot-row">
                    <div class="chat-avatar-mini bot">
                        {icon("bot", size=20, color="var(--primary)")}
                    </div>
                    <div class="bubble-bot-content">
                        <div>{content}</div>
                        {understanding_html}
                        {stepper_html}
                        <div class="msg-meta-footer">
                            <span>{esc(m_time)}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # ── Interactive Chat Input Bar ───────────────────────────────────
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        
        # Attachment expander for optional photo evidence
        with st.expander("📎 Attach Photo or Location Evidence (Optional)", expanded=False):
            uploaded_evidence = st.file_uploader(
                "Upload evidence photo",
                type=["jpg", "jpeg", "png"],
                key="chat_evidence_uploader",
                label_visibility="collapsed"
            )
            if uploaded_evidence:
                st.success(f"Attached: {uploaded_evidence.name}")

        user_input = st.chat_input(placeholder="Type your message in any language...", key="main_chat_input")
        active_prompt = pending_prompt or user_input

        # Voice input & read-aloud Web Speech API script
        st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 6px; padding: 0 4px;">
            <div style="font-size: 11.5px; color: var(--muted);">
                🔒 <strong>Citizen Privacy:</strong> Your details are encrypted & masked under Digital Public Services Standards.
            </div>
            <div style="display: flex; gap: 8px;">
                <button onclick="if('webkitSpeechRecognition' in window){var r=new webkitSpeechRecognition();r.onresult=function(e){var v=e.results[0][0].transcript;var el=document.querySelector('textarea[data-testid=stChatInputTextArea]');if(el){el.value=v;el.dispatchEvent(new Event('input',{bubbles:true}));}};r.start();}" 
                        style="background: transparent; border: 1px solid var(--border); border-radius: 999px; padding: 2px 8px; font-size: 11px; color: var(--muted); cursor: pointer;"
                        title="Voice Input (Speech-to-Text)">
                    🎙️ Voice Input
                </button>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if active_prompt:
            now_time = _format_time()
            st.session_state["messages"].append({
                "role": "user",
                "content": active_prompt,
                "time": now_time
            })

            api_client.warmup(lang)

            with st.spinner("JanSamadhan Assistant is processing..."):
                try:
                    c_state = st.session_state.get("chat_state", {})
                    c_state["lang"] = lang
                    if st.session_state.get("contact"):
                        c_state["contact"] = st.session_state["contact"]

                    res = api_client.chat(active_prompt, state=c_state)
                    reply_text = res.get("reply", "")
                    new_state = res.get("state", {})
                    meta = res.get("meta", {})
                    st.session_state["chat_state"] = new_state

                    tid = meta.get("ticket_id")
                    if tid and meta.get("found") is not False:
                        st.session_state["track_id"] = tid
                        meta["submitted_on"] = datetime.now().strftime("%d %b %Y, %I:%M %p")
                        st.session_state["last_meta"] = meta
                        if meta.get("pin"):
                            st.session_state["last_pin"] = meta["pin"]

                    st.session_state["messages"].append({
                        "role": "assistant",
                        "content": reply_text,
                        "time": _format_time(),
                        "meta": meta,
                        "status": "Submitted" if tid else None
                    })
                    st.rerun()

                except api_client.ApiError as err:
                    st.session_state["messages"].append({
                        "role": "assistant",
                        "content": f"⚠️ {err.message}",
                        "time": _format_time()
                    })
                    st.rerun()
                except Exception as ex:
                    st.session_state["messages"].append({
                        "role": "assistant",
                        "content": "⚠️ Temporary connection glitch. Please try again.",
                        "time": _format_time()
                    })
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # RIGHT COLUMN: Action & Summary Cards
    # =========================================================================
    with col_side:
        # ── Card 1: Track Your Complaint ─────────────────────────────────
        st.markdown("""
        <div class="side-card-panel">
            <div class="side-card-heading">
                <span style="color: var(--primary);">🔍</span> Track Your Complaint
            </div>
        </div>
        """, unsafe_allow_html=True)

        tr_c1, tr_c2 = st.columns([2.2, 1], vertical_alignment="center")
        with tr_c1:
            track_input_val = st.text_input(
                "Tracking ID",
                value=st.session_state.get("track_id", "GRV-1042"),
                placeholder="Enter Tracking ID (e.g. GRV-1042)",
                label_visibility="collapsed",
                key="txt_right_track_id"
            )
        with tr_c2:
            if st.button("Track", key="btn_right_track_submit", type="primary", use_container_width=True):
                norm_tid = normalize_ticket_id(track_input_val)
                if norm_tid:
                    st.session_state["track_id"] = norm_tid
                    st.switch_page("views/track.py")
                else:
                    st.warning("Please enter a valid ticket ID (e.g. GRV-1042)")

        # ── Card 2: Complaint Summary ────────────────────────────────────
        summary_data = st.session_state.get("last_meta") or {
            "ticket_id": "GRV-1042",
            "category": "Water Supply",
            "location": "Berhampur, Ganjam",
            "submitted_on": "28 Oct 2026, 10:24 AM",
            "status": "Assigned"
        }

        sum_tid = summary_data.get("ticket_id", "GRV-1042")
        sum_status = summary_data.get("status", "Assigned")
        sum_cat = summary_data.get("category", "Water Supply")
        sum_loc = summary_data.get("location", "Berhampur, Ganjam")
        sum_date = summary_data.get("submitted_on", "28 Oct 2026, 10:24 AM")

        st.markdown(f"""
        <div class="side-card-panel" style="margin-top: 14px;">
            <div class="side-card-heading">
                <span style="color: var(--primary);">📋</span> Complaint Summary
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 1.35rem; font-weight: 800; color: var(--text); letter-spacing: -0.3px;">{esc(sum_tid)}</span>
                <span style="background: var(--success-bg); color: var(--success); font-weight: 700; font-size: 12px; padding: 4px 10px; border-radius: 999px;">● {esc(sum_status)}</span>
            </div>
            <table style="width: 100%; border-collapse: collapse; font-size: 13.5px; margin-bottom: 14px;">
                <tr>
                    <td style="color: var(--muted); padding: 4px 0; width: 40%; font-weight: 500;">Category</td>
                    <td style="color: var(--text); font-weight: 600; padding: 4px 0;">: {esc(sum_cat)}</td>
                </tr>
                <tr>
                    <td style="color: var(--muted); padding: 4px 0; font-weight: 500;">Location</td>
                    <td style="color: var(--text); font-weight: 600; padding: 4px 0;">: {esc(sum_loc)}</td>
                </tr>
                <tr>
                    <td style="color: var(--muted); padding: 4px 0; font-weight: 500;">Submitted On</td>
                    <td style="color: var(--text); font-weight: 600; padding: 4px 0;">: {esc(sum_date)}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

        if st.button("View Details →", key="btn_summary_view_details", use_container_width=True):
            st.session_state["track_id"] = sum_tid
            st.switch_page("views/track.py")

        # ── Card 3: Quick Actions ────────────────────────────────────────
        st.markdown("""
        <div class="side-card-panel" style="margin-top: 14px;">
            <div class="side-card-heading">
                <span style="color: var(--primary);">⚡</span> Quick Actions
            </div>
        </div>
        """, unsafe_allow_html=True)

        qa_c1, qa_c2 = st.columns(2)
        with qa_c1:
            if st.button("📝\n\nRegister\nNew Complaint", key="btn_qa_reg_new", use_container_width=True):
                st.session_state["messages"] = []
                st.session_state["chat_state"] = {"stage": "idle", "pending": {}, "lang": lang}
                st.session_state["last_meta"] = None
                st.rerun()

            if st.button("🔔  2\n\nView\nNotifications", key="btn_qa_notif", use_container_width=True):
                st.switch_page("views/notifications.py")

        with qa_c2:
            if st.button("🔍\n\nCheck\nStatus", key="btn_qa_chk_status", use_container_width=True):
                st.switch_page("views/track.py")

            if st.button("🎧\n\nContact\nHelpline", key="btn_qa_helpline", use_container_width=True):
                st.info("📞 Citizen Grievance Helpline: 1916 / 112 (24x7 Toll-Free)")

        # ── Card 4: Together for Responsive Governance Banner Card ─────────
        st.markdown(f"""
        <div class="banner-responsive-civic" style="margin-top: 14px;">
            <div style="width: 44px; height: 44px; border-radius: 12px; background: rgba(138, 42, 150, 0.12); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                {icon("handshake", size=26, color="var(--primary)")}
            </div>
            <div>
                <div style="font-weight: 700; font-size: 14.5px; color: var(--text); line-height: 1.25;">
                    Together for<br/>Responsive Governance
                </div>
                <div style="font-size: 11.5px; color: var(--muted); margin-top: 2px;">
                    Civic redressal with accountability
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__" or "st" in globals():
    show()
