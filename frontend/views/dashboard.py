import streamlit as st
import requests
import os
from datetime import datetime

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api")

def _headers():
    token = st.session_state.get("token", "")
    return {"Authorization": f"Bearer {token}"} if token else {}

def show():
    user = st.session_state.get("user", {})

    # Welcome card
    hour = datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"

    st.markdown(f"""
    <div class="welcome-card">
        <div>
            <h2>{greeting}, {user.get('name', 'User')} 👋</h2>
            <p>Welcome to JanSamadhan Citizen Portal. How can we help you today?</p>
        </div>
        <div style="font-size:4rem;">🎓</div>
    </div>
    """, unsafe_allow_html=True)

    # Stats
    try:
        stats = requests.get(f"{API_URL}/stats", headers=_headers()).json()
    except:
        stats = {"total_users": 0, "total_tickets": 0, "open_tickets": 0, "resolved_tickets": 0, "total_messages": 0}

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="stat-card">
            <div class="stat-value">{stats.get('total_messages', 0)}</div>
            <div class="stat-label">Messages</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="stat-card" style="border-left-color:#4caf50;">
            <div class="stat-value" style="color:#4caf50;">{stats.get('resolved_tickets', 0)}</div>
            <div class="stat-label">Resolved</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="stat-card" style="border-left-color:#ff9800;">
            <div class="stat-value" style="color:#ff9800;">{stats.get('open_tickets', 0)}</div>
            <div class="stat-label">Open Tickets</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="stat-card" style="border-left-color:#9c27b0;">
            <div class="stat-value" style="color:#9c27b0;">{stats.get('total_users', 0)}</div>
            <div class="stat-label">Users</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("<div class='section-title'>💬 Recent Conversations</div>", unsafe_allow_html=True)
        try:
            sessions = requests.get(f"{API_URL}/sessions/{user['id']}", headers=_headers()).json()
        except:
            sessions = []

        if not sessions:
            st.markdown("""
            <div style="background:white;border-radius:14px;padding:2rem;text-align:center;
                        box-shadow:0 2px 10px rgba(0,0,0,0.05);color:#9e9e9e;">
                <div style="font-size:2.5rem;">💬</div>
                <div style="margin-top:0.5rem;font-size:0.9rem;">No conversations yet. Start your first chat!</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for s in sessions[:5]:
                date = s["created_at"][:10] if s.get("created_at") else ""
                st.markdown(f"""
                <div class="chat-card">
                    <div class="chat-title">💬 {s['title']}</div>
                    <div class="chat-date">🕐 {date}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Open", key=f"open_{s['id']}"):
                    st.session_state.screen = "chat"
                    st.session_state.session_id = s["id"]
                    msgs = requests.get(f"{API_URL}/messages/{s['id']}", headers=_headers()).json()
                    st.session_state.messages = [{"role": m["role"], "content": m["content"]} for m in msgs]
                    st.rerun()

    with col_right:
        st.markdown("<div class='section-title'>🚀 Quick Actions</div>", unsafe_allow_html=True)

        if st.button("➕ Start New Chat"):
            st.session_state.screen = "chat"
            st.session_state.messages = []
            st.session_state.session_id = None
            st.rerun()

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        quick = [
            "Water supply issue in my locality",
            "Streetlight not working on main street",
            "Garbage collection delayed",
            "Road damage and potholes reported",
        ]
        for q in quick:
            if st.button(q, key=f"quick_{q}"):
                st.session_state.screen = "chat"
                st.session_state.messages = []
                st.session_state.session_id = None
                st.session_state.quick_question = q
                st.rerun()

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown("<div class='logout-btn'>", unsafe_allow_html=True)
        if st.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
