import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api")

def _headers():
    token = st.session_state.get("token", "")
    return {"Authorization": f"Bearer {token}"} if token else {}

def show():
    user = st.session_state.get("user", {})

    # Header
    st.markdown(f"""
    <div class="admin-header">
        <div>
            <h2>🛡️ Admin Panel</h2>
            <p>Welcome, {user.get('name', 'Admin')} — Manage documents, tickets and users</p>
        </div>
        <div style="font-size:3rem;">⚙️</div>
    </div>
    """, unsafe_allow_html=True)

    # Stats
    try:
        stats = requests.get(f"{API_URL}/stats", headers=_headers()).json()
    except:
        stats = {"total_users": 0, "total_tickets": 0, "open_tickets": 0, "resolved_tickets": 0, "total_messages": 0}

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, val, label, color in [
        (c1, stats.get("total_users", 0), "Total Users", "#3f51b5"),
        (c2, stats.get("total_messages", 0), "Messages", "#9c27b0"),
        (c3, stats.get("total_tickets", 0), "Total Tickets", "#ff9800"),
        (c4, stats.get("open_tickets", 0), "Open", "#f44336"),
        (c5, stats.get("resolved_tickets", 0), "Resolved", "#4caf50"),
    ]:
        with col:
            st.markdown(f"""
            <div class="stat-card" style="border-top-color:{color};">
                <div class="stat-value" style="color:{color};">{val}</div>
                <div class="stat-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1.2, 2])

    # ── Left: Upload Documents ────────────────────────────────────
    with col_left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("<h4>📄 Upload Documents</h4>", unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Choose a PDF", type="pdf", label_visibility="collapsed")
        if uploaded_file:
            if st.button("🚀 Process & Index"):
                with st.spinner("Indexing..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                        res = requests.post(f"{API_URL}/upload", files=files, headers=_headers())
                        if res.status_code == 200:
                            data = res.json()
                            st.success(f"✅ {uploaded_file.name} indexed! ({data['chunks_created']} chunks)")
                        else:
                            st.error(f"❌ {res.json()['detail']}")
                    except Exception as e:
                        st.error(f"❌ {str(e)}")

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-size:0.9rem;font-weight:600;color:#424242;margin-bottom:0.5rem;'>📚 Indexed Documents</h4>", unsafe_allow_html=True)
        try:
            docs = requests.get(f"{API_URL}/documents", headers=_headers()).json()
            if docs["total"] == 0:
                st.markdown("<div style='color:#9e9e9e;font-size:0.85rem;'>No documents yet.</div>", unsafe_allow_html=True)
            else:
                for doc in docs["documents"]:
                    st.markdown(f"""
                    <div style="background:#f8f9ff;border-left:3px solid #3f51b5;border-radius:8px;
                                padding:0.5rem 0.75rem;margin-bottom:0.4rem;font-size:0.82rem;color:#424242;">
                        📄 {doc}
                    </div>
                    """, unsafe_allow_html=True)
        except:
            st.warning("⚠️ Cannot load documents")

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        st.markdown("<div class='logout-btn'>", unsafe_allow_html=True)
        if st.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Right: Tickets ────────────────────────────────────────────
    with col_right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("<h4>🎫 Support Tickets</h4>", unsafe_allow_html=True)

        search = st.text_input("🔍 Search tickets", placeholder="Search by user or issue...", label_visibility="collapsed", key="ticket_search")

        try:
            tickets = requests.get(f"{API_URL}/tickets", headers=_headers()).json()
        except:
            tickets = []

        if search:
            tickets = [t for t in tickets if search.lower() in t.get("user_name", "").lower()
                       or search.lower() in t.get("issue", "").lower()]

        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            status_filter = st.selectbox("Status", ["All", "open", "resolved"], label_visibility="collapsed", key="status_filter")
        with filter_col2:
            st.markdown(f"<div style='color:#757575;font-size:0.85rem;padding-top:0.5rem;'>{len(tickets)} tickets found</div>", unsafe_allow_html=True)

        if status_filter != "All":
            tickets = [t for t in tickets if t.get("status") == status_filter]

        if not tickets:
            st.markdown("<div style='color:#9e9e9e;font-size:0.85rem;text-align:center;padding:2rem;'>No tickets found.</div>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="ticket-row" style="font-weight:600;color:#424242;border-bottom:2px solid #e0e0e0;">
                <div style="min-width:110px;">Ticket ID</div>
                <div style="min-width:100px;">User</div>
                <div style="flex:1;">Issue</div>
                <div style="min-width:70px;">Status</div>
                <div style="min-width:90px;">Date</div>
                <div style="min-width:80px;">Action</div>
            </div>
            """, unsafe_allow_html=True)

            for t in tickets:
                badge = f'<span class="badge-open">🔴 Open</span>' if t["status"] == "open" else f'<span class="badge-resolved">🟢 Done</span>'
                date = t["created_at"][:10] if t.get("created_at") else ""
                st.markdown(f"""
                <div class="ticket-row">
                    <div class="ticket-id">{t['id']}</div>
                    <div class="ticket-user">{t.get('user_name','—')}</div>
                    <div class="ticket-issue" title="{t['issue']}">{t['issue'][:60]}...</div>
                    <div>{badge}</div>
                    <div class="ticket-date">{date}</div>
                </div>
                """, unsafe_allow_html=True)

                if t["status"] == "open":
                    st.markdown("<div class='resolve-btn'>", unsafe_allow_html=True)
                    if st.button("✅ Resolve", key=f"resolve_{t['id']}"):
                        try:
                            requests.patch(f"{API_URL}/tickets/{t['id']}", json={"status": "resolved"}, headers=_headers())
                            st.rerun()
                        except:
                            st.error("Failed to update")
                    st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
