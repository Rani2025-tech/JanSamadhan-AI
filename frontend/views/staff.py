"""
JanSamadhan Staff Workbench & Administration View.
Provides department officials and super administrators with live operational triage,
ticket lifecycle actions, SLA tracking, misroute handling, and duplicate cluster inspection.
English-only view; dynamic data never cached to prevent session leak.
"""

import os
import json
from html import escape as esc
from typing import Optional, Dict, Any, List
import pandas as pd
import streamlit as st

import api_client
from auth_helpers import is_staff_session_valid, clear_staff_session
from components import ticket_card, normalize_ticket_id
from staff_helpers import (
    format_ist,
    sla_label,
    allowed_next_statuses,
    build_filters
)

# Note: In JanSamadhan, the frontend and backend are deployed from the same repository,
# so data/departments.json is accessible from the repository root.
def _load_department_catalog() -> List[Dict[str, Any]]:
    """Loads department and category taxonomy excluding catch-all review category."""
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dept_file = os.path.join(repo_root, "data", "departments.json")
    if os.path.exists(dept_file):
        try:
            with open(dept_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [
                    d for d in data
                    if str(d.get("category", "")).lower() != "other / needs review"
                    and str(d.get("department", "")).lower() != "general administration / grievance cell"
                ]
        except Exception:
            pass
    return []

def _format_avg_res(hours: Any) -> str:
    """Formats resolution hours: hours below 48, days from 48."""
    if hours is None:
        return "N/A"
    try:
        h = float(hours)
        if h < 48:
            return f"{h:.1f} hrs"
        days = h / 24.0
        return f"{days:.1f} days"
    except (ValueError, TypeError):
        return "N/A"

def show():
    # ── 1. Guard & Authentication Verification ───────────────────────────
    if not is_staff_session_valid():
        try:
            st.switch_page("views/home.py")
        except Exception:
            st.rerun()
        return

    token = st.session_state.get("token", "")
    staff_name = st.session_state.get("staff_name") or "Staff Member"
    role = str(st.session_state.get("role") or "DEPARTMENT_OFFICIAL").upper()
    department = st.session_state.get("department") or "All departments"

    # ── 2. Staff Header & Session Controls ──────────────────────────────
    col_hdr, col_btn = st.columns([4, 1])
    with col_hdr:
        st.markdown(f"""
        <div style="margin-bottom: 0.75rem;">
            <h2 style="margin: 0; font-size: 1.6rem; color: var(--primary);">🏛️ Staff Portal</h2>
            <p style="margin: 3px 0 0 0; color: var(--muted); font-size: 14.5px;">
                Signed in as <strong>{esc(staff_name)}</strong> ({esc(role)}, {esc(department)})
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_btn:
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        if st.button("🚪 Logout", key="btn_staff_header_logout", use_container_width=True):
            clear_staff_session()
            try:
                st.switch_page("views/home.py")
            except Exception:
                st.rerun()
            return

    # ── 3. Tabs Setup ───────────────────────────────────────────────────
    # [Admin Tabs Placeholder] Future phases will add: Analytics, Hotspots, Review queue, Staff and Audit
    tab_workbench, tab_clusters = st.tabs(["Workbench", "Clusters"])

    # ═════════════════════════════════════════════════════════════════════
    # TAB 1: WORKBENCH
    # ═════════════════════════════════════════════════════════════════════
    with tab_workbench:
        # ── A. KPI Cards from admin_stats ───────────────────────────────
        try:
            stats = api_client.admin_stats(token)
        except api_client.ApiError as e:
            st.error(f"Failed to load operational metrics: {e.message}")
            stats = {}

        total_cnt = stats.get("total", 0)
        open_cnt = stats.get("open", 0)
        overdue_cnt = stats.get("overdue_count", 0)
        resolved_cnt = stats.get("resolved", 0)
        avg_res = _format_avg_res(stats.get("avg_resolution_hours"))

        st.markdown(f"""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 1.5rem;">
            <div class="panel-card" style="padding: 14px 18px; border-left: 4px solid var(--primary); background: var(--card);">
                <div style="font-size: 12px; font-weight: 600; color: var(--muted); text-transform: uppercase;">Total Tickets</div>
                <div style="font-size: 26px; font-weight: 700; color: var(--text); margin-top: 2px;">{esc(str(total_cnt))}</div>
            </div>
            <div class="panel-card" style="padding: 14px 18px; border-left: 4px solid #3B82F6; background: var(--card);">
                <div style="font-size: 12px; font-weight: 600; color: var(--muted); text-transform: uppercase;">Open</div>
                <div style="font-size: 26px; font-weight: 700; color: #1D4ED8; margin-top: 2px;">{esc(str(open_cnt))}</div>
            </div>
            <div class="panel-card" style="padding: 14px 18px; border-left: 4px solid #EF4444; background: var(--card);">
                <div style="font-size: 12px; font-weight: 600; color: var(--muted); text-transform: uppercase;">Overdue</div>
                <div style="font-size: 26px; font-weight: 700; color: #B91C1C; margin-top: 2px;">{esc(str(overdue_cnt))}</div>
            </div>
            <div class="panel-card" style="padding: 14px 18px; border-left: 4px solid var(--success); background: var(--card);">
                <div style="font-size: 12px; font-weight: 600; color: var(--muted); text-transform: uppercase;">Resolved</div>
                <div style="font-size: 26px; font-weight: 700; color: var(--success); margin-top: 2px;">{esc(str(resolved_cnt))}</div>
            </div>
            <div class="panel-card" style="padding: 14px 18px; border-left: 4px solid var(--medium); background: var(--card);">
                <div style="font-size: 12px; font-weight: 600; color: var(--muted); text-transform: uppercase;">Avg Resolution</div>
                <div style="font-size: 26px; font-weight: 700; color: var(--text); margin-top: 2px;">{esc(avg_res)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── B. Filter Controls in Expander ───────────────────────────────
        with st.expander("🔍 Filter & Search Grievances", expanded=False):
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            with f_col1:
                status_filter = st.selectbox(
                    "Status",
                    ["All", "Submitted", "Assigned", "In Progress", "Resolved", "Reopened"],
                    index=0,
                    key="sb_filter_status"
                )
            with f_col2:
                priority_filter = st.selectbox(
                    "Priority",
                    ["All", "Critical", "High", "Medium", "Low"],
                    index=0,
                    key="sb_filter_priority"
                )
            with f_col3:
                lang_disp = st.selectbox(
                    "Language",
                    ["All", "English", "Hindi", "Odia"],
                    index=0,
                    key="sb_filter_lang"
                )
                lang_map = {"English": "en", "Hindi": "hi", "Odia": "or"}
                lang_val = lang_map.get(lang_disp, lang_disp)
            with f_col4:
                area_filter = st.text_input("Area / Locality", placeholder="e.g. Saheed Nagar", key="txt_filter_area")

            f_col5, f_col6, f_col7, f_col8 = st.columns(4)
            with f_col5:
                st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
                overdue_only = st.checkbox("Overdue only", value=False, key="chk_filter_overdue")
            with f_col6:
                st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
                needs_review_only = st.checkbox("Needs review only", value=False, key="chk_filter_review")
            with f_col7:
                search_ticket = st.text_input("Ticket ID Search", placeholder="e.g. GRV-1002", key="txt_filter_tid")
            with f_col8:
                limit_filter = st.selectbox("Limit", [25, 50, 100, 200], index=1, key="sb_filter_limit")

            # Department filter (ADMIN only; hidden for officials)
            dept_filter = "All"
            if role == "ADMIN":
                cat_list = _load_department_catalog()
                all_depts = sorted(list(set(d["department"] for d in cat_list if d.get("department"))))
                dept_filter = st.selectbox("Department (Admin Scoping)", ["All"] + all_depts, index=0, key="sb_filter_dept")

            f_btn_col1, _ = st.columns([1, 4])
            with f_btn_col1:
                refresh_clicked = st.button("🔄 Refresh Data", key="btn_refresh_tickets", use_container_width=True)

        # Build query parameters
        query_kwargs = {
            "status": status_filter,
            "priority": priority_filter,
            "language": lang_val,
            "area": area_filter,
            "overdue_only": overdue_only,
            "needs_review_only": needs_review_only,
            "limit": limit_filter,
        }
        if role == "ADMIN" and dept_filter != "All":
            query_kwargs["department"] = dept_filter

        query_params = build_filters(**query_kwargs)

        # ── C. Ticket Table via list_grievances ───────────────────────────
        try:
            tickets = api_client.list_grievances(token, filters=query_params)
        except api_client.ApiError as e:
            st.error(f"Failed to fetch grievances: {e.message}")
            tickets = []

        # Client-side filter by ticket ID if specified
        norm_search = normalize_ticket_id(search_ticket)
        if norm_search:
            tickets = [t for t in tickets if t.get("ticket_id") == norm_search]

        if not tickets:
            st.info("No grievances match the current filter criteria.")
            selected_ticket_id = None
        else:
            # Sort: Overdue and Critical first, then newest
            def _ticket_sort_key(t):
                is_overdue = 1 if t.get("overdue") else 0
                pri_map = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
                pri_val = pri_map.get(t.get("priority", "Medium"), 0)
                return (is_overdue, pri_val, t.get("created_at") or "")

            tickets.sort(key=_ticket_sort_key, reverse=True)

            table_rows = []
            for t in tickets:
                table_rows.append({
                    "Ticket": t.get("ticket_id"),
                    "Priority": t.get("priority"),
                    "Status": t.get("status"),
                    "Department": t.get("department"),
                    "Category": t.get("category"),
                    "Area": t.get("area") or t.get("location") or "-",
                    "Language": str(t.get("language") or "en").upper(),
                    "SLA": sla_label(t.get("sla_due_at"), t.get("status")),
                    "Review": "⚠️ Yes" if t.get("needs_review") else "No",
                    "Cluster": t.get("cluster_id") or "-"
                })

            df_tickets = pd.DataFrame(table_rows)

            st.markdown('<div style="overflow-x: auto; margin-bottom: 1rem;">', unsafe_allow_html=True)
            
            selected_ticket_id = st.session_state.get("staff_selected_ticket_id")
            native_selection_success = False

            try:
                event = st.dataframe(
                    df_tickets,
                    use_container_width=True,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row"
                )
                if hasattr(event, "selection") and hasattr(event.selection, "rows"):
                    selected_rows = event.selection.rows
                    if selected_rows:
                        row_idx = selected_rows[0]
                        selected_ticket_id = df_tickets.iloc[row_idx]["Ticket"]
                        st.session_state["staff_selected_ticket_id"] = selected_ticket_id
                native_selection_success = True
            except (TypeError, AttributeError):
                native_selection_success = False

            st.markdown('</div>', unsafe_allow_html=True)

            # Fallback selector or quick dropdown selector
            ticket_options = [t.get("ticket_id") for t in tickets if t.get("ticket_id")]
            if not native_selection_success or not selected_ticket_id:
                default_idx = 0
                if selected_ticket_id in ticket_options:
                    default_idx = ticket_options.index(selected_ticket_id)
                picked = st.selectbox(
                    "Select Grievance for Detailed Inspection & Action:",
                    ticket_options,
                    index=default_idx,
                    key="sb_ticket_select_fallback"
                )
                selected_ticket_id = picked
                st.session_state["staff_selected_ticket_id"] = selected_ticket_id

        # ── D. Detail Panel for Selected Ticket ───────────────────────────
        if selected_ticket_id:
            st.markdown("---")
            st.markdown(f"### 📋 Ticket Detail: `{esc(selected_ticket_id)}`")

            try:
                ticket_data = api_client.get_ticket(selected_ticket_id, token=token)
            except api_client.ApiError as e:
                st.error(f"Failed to fetch ticket record: {e.message}")
                ticket_data = None

            if not ticket_data:
                st.warning("Selected ticket record could not be retrieved.")
            else:
                col_d1, col_d2 = st.columns([1, 1])
                with col_d1:
                    # Ticket Card from components
                    st.markdown(ticket_card(ticket_data, lang="en"), unsafe_allow_html=True)

                    # Contact and Location details
                    c_name = ticket_data.get("contact_name") or "Anonymous Citizen"
                    c_phone = ticket_data.get("contact_phone") or "Not provided"
                    loc_val = ticket_data.get("location") or "Not specified"
                    area_val = ticket_data.get("area") or "Not specified"
                    sla_due = ticket_data.get("sla_due_at")

                    st.markdown(f"""
                    <div class="panel-card" style="margin-top: 14px; padding: 18px; background: var(--card); border: 1px solid var(--border);">
                        <h4 style="margin: 0 0 12px 0; font-size: 15px; color: var(--primary);">👤 Citizen & Operational Details</h4>
                        <table style="width: 100%; border-collapse: collapse; font-size: 13.5px;">
                            <tr style="border-bottom: 1px solid var(--border);">
                                <td style="padding: 6px 0; color: var(--muted); font-weight: 600;">Citizen Name</td>
                                <td style="padding: 6px 0; color: var(--text);">{esc(c_name)}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid var(--border);">
                                <td style="padding: 6px 0; color: var(--muted); font-weight: 600;">Contact Phone</td>
                                <td style="padding: 6px 0; color: var(--text);">{esc(c_phone)}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid var(--border);">
                                <td style="padding: 6px 0; color: var(--muted); font-weight: 600;">Reported Location</td>
                                <td style="padding: 6px 0; color: var(--text);">{esc(loc_val)}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid var(--border);">
                                <td style="padding: 6px 0; color: var(--muted); font-weight: 600;">Ward / Area</td>
                                <td style="padding: 6px 0; color: var(--text);">{esc(area_val)}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid var(--border);">
                                <td style="padding: 6px 0; color: var(--muted); font-weight: 600;">Routing Reason</td>
                                <td style="padding: 6px 0; color: var(--text);">{esc(ticket_data.get("routing_reason") or "Auto-routed")} (Conf: {ticket_data.get("confidence", 0.0):.2f})</td>
                            </tr>
                            <tr style="border-bottom: 1px solid var(--border);">
                                <td style="padding: 6px 0; color: var(--muted); font-weight: 600;">Escalation Level</td>
                                <td style="padding: 6px 0; color: var(--text);">Level {esc(str(ticket_data.get("escalation_level", 0)))}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid var(--border);">
                                <td style="padding: 6px 0; color: var(--muted); font-weight: 600;">Cluster ID</td>
                                <td style="padding: 6px 0; color: var(--text);">{esc(ticket_data.get("cluster_id") or "None")}</td>
                            </tr>
                            <tr>
                                <td style="padding: 6px 0; color: var(--muted); font-weight: 600;">SLA Due (IST)</td>
                                <td style="padding: 6px 0; color: var(--text);">{esc(format_ist(sla_due))} ({esc(sla_label(sla_due, ticket_data.get("status")))})</td>
                            </tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)

                with col_d2:
                    # Complaint Texts & Summary
                    raw_text = ticket_data.get("text_raw") or "No text recorded"
                    en_text = ticket_data.get("text_en") or ""
                    summary = ticket_data.get("summary") or "No summary available"

                    st.markdown(f"""
                    <div class="panel-card" style="padding: 18px; background: var(--card); border: 1px solid var(--border); margin-bottom: 14px;">
                        <h4 style="margin: 0 0 8px 0; font-size: 15px; color: var(--primary);">📝 Complaint Content</h4>
                        <div style="font-size: 12px; font-weight: 600; color: var(--muted); margin-bottom: 4px;">Original Statement</div>
                        <div style="background: var(--bg); padding: 10px 14px; border-radius: var(--radius-sm); font-size: 13.5px; color: var(--text); line-height: 1.4; margin-bottom: 10px;">
                            {esc(raw_text)}
                        </div>
                    """, unsafe_allow_html=True)

                    if en_text and en_text.strip().lower() != raw_text.strip().lower():
                        st.markdown(f"""
                        <div style="font-size: 12px; font-weight: 600; color: var(--muted); margin-bottom: 4px;">English Translation</div>
                        <div style="background: var(--bg); padding: 10px 14px; border-radius: var(--radius-sm); font-size: 13.5px; color: var(--text); line-height: 1.4; margin-bottom: 10px;">
                            {esc(en_text)}
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown(f"""
                        <div style="font-size: 12px; font-weight: 600; color: var(--muted); margin-bottom: 4px;">Issue Summary</div>
                        <div style="font-size: 13.5px; color: var(--text); line-height: 1.4;">
                            {esc(summary)}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # ── E. Update Status Form ─────────────────────────────
                    curr_status = ticket_data.get("status", "Submitted")
                    next_options = allowed_next_statuses(curr_status)

                    st.markdown("""
                    <div class="panel-card" style="padding: 18px; background: var(--card); border: 1px solid var(--border); margin-bottom: 14px;">
                        <h4 style="margin: 0 0 8px 0; font-size: 15px; color: var(--primary);">⚡ Update Lifecycle Status</h4>
                    """, unsafe_allow_html=True)

                    if not next_options:
                        st.info(f"Grievance is currently '{curr_status}'. No further status updates permitted.")
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        with st.form("form_ticket_status_update"):
                            target_status = st.selectbox("Next Status Transition:", next_options)
                            status_note = st.text_area(
                                "Official Action / Resolution Note:",
                                placeholder="Describe investigation, repair dispatch, or resolution action taken (min 5 chars)..."
                            )
                            submit_status = st.form_submit_button("Update Status", type="primary")

                            if submit_status:
                                clean_note = status_note.strip()
                                if target_status == "Resolved" and len(clean_note) < 5:
                                    st.error("A resolution note of at least 5 characters is mandatory when resolving a ticket.")
                                elif clean_note and len(clean_note) < 5:
                                    st.error("Note must be at least 5 characters.")
                                else:
                                    try:
                                        api_client.update_status(token, selected_ticket_id, target_status, note=clean_note)
                                        st.success(f"Status updated to '{target_status}' successfully.")
                                        st.rerun()
                                    except api_client.ApiError as err:
                                        st.error(f"Status update failed: {err.message}")

                        st.markdown("</div>", unsafe_allow_html=True)

                    # ── F. Role-Specific Action Drawers ──────────────────
                    if role == "DEPARTMENT_OFFICIAL":
                        if curr_status != "Resolved":
                            with st.expander("🚩 Flag as Misrouted", expanded=False):
                                st.caption("Flag this ticket if it falls outside your department jurisdiction. It will appear for administrative re-routing.")
                                flag_note = st.text_area("Reason for Flagging (min 5 chars):", key="txt_misroute_reason")
                                if st.button("Submit Misroute Flag", key="btn_submit_flag"):
                                    if len(flag_note.strip()) < 5:
                                        st.error("Flagging reason must be at least 5 characters.")
                                    else:
                                        try:
                                            api_client.flag_misrouted(token, selected_ticket_id, flag_note.strip())
                                            st.success("Ticket flagged as misrouted successfully.")
                                            st.rerun()
                                        except api_client.ApiError as err:
                                            st.error(f"Flagging failed: {err.message}")

                    if role == "ADMIN":
                        with st.expander("🔄 Re-route Grievance (Admin)", expanded=False):
                            st.caption("Re-assign this grievance to the appropriate municipal department and category.")
                            catalog = _load_department_catalog()
                            dept_cat_map = {}
                            for item in catalog:
                                d_name = item.get("department")
                                c_name = item.get("category")
                                if d_name and c_name:
                                    dept_cat_map.setdefault(d_name, []).append(c_name)

                            dept_opts = sorted(list(dept_cat_map.keys()))
                            if not dept_opts:
                                st.warning("Department catalog could not be loaded.")
                            else:
                                sel_target_dept = st.selectbox("Target Department:", dept_opts, key="sb_target_dept")
                                cat_opts = sorted(dept_cat_map.get(sel_target_dept, []))
                                sel_target_cat = st.selectbox("Target Category:", cat_opts, key="sb_target_cat")
                                reroute_note = st.text_area("Administrative Re-routing Reason (min 5 chars):", key="txt_reroute_reason")

                                if st.button("Confirm Re-routing", key="btn_confirm_reroute", type="primary"):
                                    if len(reroute_note.strip()) < 5:
                                        st.error("Re-routing reason must be at least 5 characters.")
                                    else:
                                        try:
                                            api_client.reroute(token, selected_ticket_id, sel_target_dept, sel_target_cat, reroute_note.strip())
                                            st.success(f"Ticket successfully re-routed to '{sel_target_dept}'.")
                                            st.rerun()
                                        except api_client.ApiError as err:
                                            st.error(f"Re-routing failed: {err.message}")

                # ── G. Full History Timeline ──────────────────────────────
                st.markdown("#### 📜 Audit History & Timeline")
                hist_records = ticket_data.get("history") or []
                if not hist_records:
                    st.caption("No historical events recorded for this ticket.")
                else:
                    st.markdown("""
                    <div style="background: var(--card); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 12px 16px;">
                    """, unsafe_allow_html=True)
                    for idx, h in enumerate(hist_records):
                        h_time = format_ist(h.get("created_at"))
                        h_status = h.get("status") or "-"
                        h_actor = h.get("actor") or "System"
                        h_note = h.get("note") or ""

                        st.markdown(f"""
                        <div style="padding: 10px 0; border-bottom: {'1px solid var(--border)' if idx < len(hist_records) - 1 else 'none'};">
                            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 13px;">
                                <span><strong>{esc(h_status)}</strong> • <span style="color: var(--muted);">{esc(h_actor)}</span></span>
                                <span style="color: var(--muted); font-size: 12px;">{esc(h_time)}</span>
                            </div>
                            {f'<div style="margin-top: 4px; font-size: 13px; color: var(--text);">{esc(h_note)}</div>' if h_note else ''}
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

    # ═════════════════════════════════════════════════════════════════════
    # TAB 2: CLUSTERS
    # ═════════════════════════════════════════════════════════════════════
    with tab_clusters:
        st.markdown("### 🗂️ Active Civic Duplicate Clusters")
        st.caption("Municipal issues automatically clustered by semantic similarity and geographic proximity.")

        try:
            clusters_list = api_client.admin_clusters(token)
        except api_client.ApiError as err:
            st.error(f"Failed to fetch cluster data: {err.message}")
            clusters_list = []

        if not clusters_list:
            st.info("No active duplicate clusters found.")
        else:
            cl_rows = []
            for c in clusters_list:
                cl_rows.append({
                    "Cluster ID": c.get("cluster_id"),
                    "Department": c.get("department"),
                    "Category": c.get("category"),
                    "Area": c.get("area") or "-",
                    "Reports": c.get("report_count", 1),
                    "First Reported (IST)": format_ist(c.get("first_reported_at")),
                    "Last Reported (IST)": format_ist(c.get("last_reported_at")),
                    "Representative Ticket": c.get("representative_ticket_id") or "-"
                })

            df_cl = pd.DataFrame(cl_rows)
            st.markdown('<div style="overflow-x: auto; margin-bottom: 1.5rem;">', unsafe_allow_html=True)
            st.dataframe(df_cl, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### 🔍 Open Cluster Representative in Workbench")
            c_col1, c_col2 = st.columns([3, 1])
            with c_col1:
                rep_input = st.text_input("Representative Ticket ID:", placeholder="e.g. GRV-1003", key="txt_cluster_open_rep")
            with c_col2:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("Inspect in Workbench", key="btn_open_rep_ticket", use_container_width=True):
                    norm_rep = normalize_ticket_id(rep_input)
                    if norm_rep:
                        st.session_state["staff_selected_ticket_id"] = norm_rep
                        st.success(f"Ticket {norm_rep} selected. Switch to Workbench tab to inspect.")
                        st.rerun()
                    else:
                        st.error("Invalid ticket ID format.")

if __name__ == "__main__" or "st" in globals():
    show()
