import streamlit as st
from ui_text import ui
import api_client
from components import (
    normalize_ticket_id,
    normalize_pin,
    ticket_card,
    stepper,
    build_receipt,
    status_pill,
    esc
)

@st.cache_data(ttl=5)
def fetch_public_ticket(ticket_id: str):
    """Caches public ticket fetch for 5 seconds to reduce redundant network roundtrips."""
    return api_client.get_ticket(ticket_id)

def show():
    if "lang" not in st.session_state:
        st.session_state["lang"] = "en"
    lang = st.session_state["lang"]

    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <h2 style="margin: 0; font-size: 1.6rem;">🔍 {esc(ui('track_title', lang))}</h2>
        <p style="margin: 4px 0 0 0; color: var(--muted); font-size: 14.5px;">{esc(ui('track_subtitle', lang))}</p>
    </div>
    """, unsafe_allow_html=True)

    # Search Bar & Refresh Row
    col_input, col_btn, col_ref = st.columns([3, 1, 1])
    with col_input:
        raw_id = st.text_input(
            "Ticket ID",
            value=st.session_state.get("track_id", ""),
            placeholder=ui("track_placeholder", lang),
            label_visibility="collapsed",
            key="track_page_input"
        )
    with col_btn:
        search_clicked = st.button(ui("track_button", lang), key="btn_track_search", type="primary", use_container_width=True)
    with col_ref:
        if st.button(f"🔄 {ui('refresh', lang)}", key="btn_track_refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    norm_id = normalize_ticket_id(raw_id)
    if search_clicked and norm_id:
        st.session_state["track_id"] = norm_id
        st.rerun()

    active_id = norm_id or normalize_ticket_id(st.session_state.get("track_id", ""))

    if not active_id:
        st.info(f"👉 {ui('track_placeholder', lang)}")
        return

    # Check staff login
    staff_token = st.session_state.get("token") or st.session_state.get("admin_token")
    is_staff = bool(staff_token)

    # Fetch Ticket
    with st.spinner("Fetching status..."):
        try:
            if is_staff:
                ticket = api_client.get_ticket(active_id, token=staff_token)
            else:
                ticket = fetch_public_ticket(active_id)
        except Exception:
            ticket = None

    if not ticket:
        st.warning(f"❌ {ui('not_found', lang)} ({active_id})")
        return

    # 1. Main Ticket Details Card
    st.markdown(ticket_card(ticket, lang), unsafe_allow_html=True)

    # 2. Status Progression Stepper
    history = ticket.get("history") or []
    status_str = ticket.get("status", "Submitted")
    st.markdown(stepper(status_str, history, lang), unsafe_allow_html=True)

    # 3. Full History Timeline
    st.markdown(f'<h4 style="margin: 1.5rem 0 0.75rem 0; font-size: 1.15rem;">📜 {esc(ui("audit_timeline_title", lang))}</h4>', unsafe_allow_html=True)
    if history:
        for item in history:
            s_val = item.get("status", "")
            t_val = item.get("created_at", "")
            actor_val = item.get("actor", "System")
            note_val = item.get("note", "")

            note_line = f'<div style="font-size: 13.5px; margin-top: 4px; color: var(--text);">{esc(note_val)}</div>' if note_val else ''
            st.markdown(f"""
            <div style="background: var(--card); border-left: 3px solid var(--primary); border-radius: var(--radius-sm); padding: 10px 14px; margin-bottom: 8px; box-shadow: var(--shadow-sm);">
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 13px;">
                    <span style="font-weight: 700; color: var(--primary);">{esc(s_val)} ({esc(actor_val)})</span>
                    <span style="color: var(--muted); font-size: 12px;">{esc(t_val)}</span>
                </div>
                {note_line}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption(ui("no_history_note", lang))

    # 4. Private Details & Receipt Download Section
    if is_staff:
        # Staff view: unmasked details already present, skip PIN box
        st.markdown(f"""
        <div class="panel-card" style="margin-top: 1.25rem; border: 1.5px solid var(--primary); background: var(--card);">
            <h4 style="margin: 0 0 10px 0; color: var(--primary);">👤 Citizen Contact & Full Complaint (Staff View)</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 10px;">
                <div>
                    <span class="understanding-label">Citizen Name</span>
                    <div style="font-weight: 600; font-size: 14.5px;">{esc(ticket.get('citizen_name') or 'Anonymous')}</div>
                </div>
                <div>
                    <span class="understanding-label">Contact</span>
                    <div style="font-weight: 600; font-size: 14.5px;">{esc(ticket.get('contact') or 'None')}</div>
                </div>
                <div>
                    <span class="understanding-label">{esc(ui('location', lang))}</span>
                    <div style="font-weight: 600; font-size: 14.5px;">{esc(ticket.get('location') or 'Not specified')}</div>
                </div>
            </div>
            <div style="margin-top: 8px;">
                <span class="understanding-label">Original Complaint Text</span>
                <p style="margin: 4px 0 0 0; font-size: 14px; color: var(--text); background: var(--bg); padding: 8px 12px; border-radius: var(--radius-sm);">{esc(ticket.get('original_text') or '')}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
        receipt_data = build_receipt(ticket, lang)
        st.download_button(
            label=f"📥 {ui('download_receipt', lang)}",
            data=receipt_data,
            file_name=f"JanSamadhan_Receipt_{active_id}.txt",
            mime="text/plain",
            key="btn_track_dl_receipt_staff"
        )
    else:
        # Citizen public view: Check if active_id is unlocked
        unlocked_tickets = st.session_state.get("unlocked_tickets", {})
        unlocked_record = unlocked_tickets.get(active_id)

        if unlocked_record:
            st.markdown(f"""
            <div class="panel-card" style="margin-top: 1.25rem; border: 1.5px solid var(--primary); background: var(--card);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h4 style="margin: 0; color: var(--primary);">🔓 {esc(ui('unlock_title', lang))}</h4>
                    <span style="font-size: 12px; color: var(--success); font-weight: 600; background: var(--success-bg); padding: 3px 8px; border-radius: 999px;">{esc(ui('verified_badge', lang))}</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 10px;">
                    <div>
                        <span class="understanding-label">{esc(ui('citizen_name_label', lang))}</span>
                        <div style="font-weight: 600; font-size: 14.5px;">{esc(unlocked_record.get('citizen_name') or 'Anonymous')}</div>
                    </div>
                    <div>
                        <span class="understanding-label">{esc(ui('contact_label', lang))}</span>
                        <div style="font-weight: 600; font-size: 14.5px;">{esc(unlocked_record.get('contact') or 'None')}</div>
                    </div>
                    <div>
                        <span class="understanding-label">{esc(ui('location', lang))}</span>
                        <div style="font-weight: 600; font-size: 14.5px;">{esc(unlocked_record.get('location') or 'Not specified')}</div>
                    </div>
                </div>
                <div style="margin-top: 8px;">
                    <span class="understanding-label">{esc(ui('summary_title', lang))}</span>
                    <p style="margin: 4px 0 8px 0; font-size: 14px; color: var(--text);">{esc(unlocked_record.get('summary') or '')}</p>
                </div>
                <div style="margin-top: 8px;">
                    <span class="understanding-label">{esc(ui('original_text_label', lang))}</span>
                    <p style="margin: 4px 0 0 0; font-size: 14px; color: var(--text); background: var(--bg); padding: 8px 12px; border-radius: var(--radius-sm);">{esc(unlocked_record.get('original_text') or '')}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            pin_for_receipt = (
                st.session_state.get("unlocked_pins", {}).get(active_id)
                or (st.session_state.get("last_pin") if st.session_state.get("last_ticket") == active_id else None)
            )
            st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
            receipt_data = build_receipt(unlocked_record, lang, pin=pin_for_receipt)
            st.download_button(
                label=f"📥 {ui('download_receipt', lang)}",
                data=receipt_data,
                file_name=f"JanSamadhan_Receipt_{active_id}.txt",
                mime="text/plain",
                key="btn_track_dl_receipt_unlocked"
            )
        else:
            st.markdown(f"""
            <div class="panel-card" style="margin-top: 1.25rem; border: 1px dashed var(--border);">
                <h4 style="margin: 0 0 6px 0; color: var(--text);">🔒 {esc(ui('unlock_title', lang))}</h4>
                <p style="margin: 0 0 10px 0; font-size: 13.5px; color: var(--muted);">{esc(ui('details_locked_hint', lang))}</p>
            </div>
            """, unsafe_allow_html=True)

            with st.form(key=f"unlock_form_{active_id}"):
                col_pin, col_sub = st.columns([3, 1])
                with col_pin:
                    pin_input = st.text_input(
                        "Tracking PIN",
                        type="password",
                        max_chars=6,
                        placeholder=ui("pin_placeholder", lang),
                        label_visibility="collapsed",
                        key=f"pin_in_{active_id}"
                    )
                with col_sub:
                    unlock_submitted = st.form_submit_button(ui("unlock_button", lang), type="primary", use_container_width=True)

            if unlock_submitted:
                norm_pin = normalize_pin(pin_input)
                if not norm_pin:
                    st.warning(f"⚠️ {ui('wrong_credentials', lang)}")
                else:
                    try:
                        res = api_client.private_ticket(active_id, norm_pin)
                        st.session_state.setdefault("unlocked_tickets", {})[active_id] = res
                        st.session_state.setdefault("unlocked_pins", {})[active_id] = norm_pin
                        st.rerun()
                    except api_client.ApiError as err:
                        st.error(err.message)
                    except Exception as e:
                        st.error(f"Error: {e}")

            st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
            receipt_data = build_receipt(ticket, lang)
            st.download_button(
                label=f"📥 {ui('download_receipt', lang)}",
                data=receipt_data,
                file_name=f"JanSamadhan_Receipt_{active_id}.txt",
                mime="text/plain",
                key="btn_track_dl_receipt_public"
            )

    # 5. Citizen Feedback Form for Resolved Tickets
    if status_str.lower() == "resolved":
        st.markdown(f"""
        <div class="panel-card" style="margin-top: 1.5rem; border: 1.5px solid var(--primary);">
            <h4 style="margin: 0 0 8px 0; color: var(--primary);">⭐ {esc(ui('rate_title', lang))}</h4>
            <p style="margin: 0 0 12px 0; font-size: 13.5px; color: var(--muted);">How satisfied are you with the resolution of this grievance? Please rate your experience.</p>
        </div>
        """, unsafe_allow_html=True)

        rating_val = 5
        if hasattr(st, "feedback"):
            star_idx = st.feedback("stars", key="resolved_feedback_stars")
            rating_val = (star_idx + 1) if star_idx is not None else 5
        else:
            rating_val = st.radio("Rating", [1, 2, 3, 4, 5], index=4, horizontal=True)

        comment_txt = st.text_area("Additional Feedback (Optional)", placeholder="Write your comments here...", key="resolved_feedback_comment")

        if st.button(ui("rate_submit", lang), type="primary", key="btn_submit_feedback"):
            try:
                res = api_client.send_feedback(active_id, rating_val, comment_txt)
                st.success(f"✅ {ui('thanks', lang)}")
                if res.get("reopened") or rating_val <= 2:
                    st.warning(f"⚠️ {ui('reopened_note', lang)}")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Failed to submit feedback: {e}")

if __name__ == "__main__" or "st" in globals():
    show()
