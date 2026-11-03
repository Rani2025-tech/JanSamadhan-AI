import streamlit as st
import api_client
from auth_helpers import is_staff_session_valid, set_staff_session
from components import esc

def show():
    # If already logged in with a valid session, route directly to staff page
    if is_staff_session_valid():
        try:
            st.switch_page("views/staff.py")
        except Exception:
            st.rerun()
        return

    st.markdown("""
    <div class="brand-wrap" style="text-align: center; margin-bottom: 2rem;">
        <div class="brand-icon" style="margin: 0 auto 12px auto;">JS</div>
        <h1 style="margin: 0; font-size: 1.8rem;">JanSamadhan Staff Portal</h1>
        <p style="margin: 4px 0 0 0; color: var(--muted); font-size: 14.5px;">Authorized municipal officer & administrative sign-in</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("staff_login_form"):
        email = st.text_input("Staff Email address", placeholder="officer@jansamadhan.local", key="staff_login_email")
        password = st.text_input("Password", type="password", placeholder="••••••••", key="staff_login_pass")
        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
        login_submitted = st.form_submit_button("Sign In to Portal", type="primary", use_container_width=True)

    if login_submitted:
        if not email or not password:
            st.warning("Please enter both email and password.")
        else:
            try:
                res = api_client.login(email, password)
                set_staff_session(res)
                st.success(f"Signed in as {res.get('name', 'Staff')} ({res.get('role')})")
                # TODO: Next phase replaces this temporary routing with role-specific dashboards (Admin / Department Official)
                try:
                    st.switch_page("views/staff.py")
                except Exception:
                    st.rerun()
            except api_client.ApiError as err:
                st.error(f"❌ {err.message}")
            except Exception as e:
                st.error(f"❌ Login failed: {e}")

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    if st.button("← Back to Home", key="btn_login_back_home"):
        try:
            st.switch_page("views/home.py")
        except Exception:
            st.rerun()

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 12px 16px; font-size: 13px; color: var(--muted); line-height: 1.4;">
        🔒 <strong>Staff Security Notice:</strong> Public citizen registration is discontinued. Citizens submit and track grievances freely without an account. Only authorized municipal personnel (ADMIN or DEPARTMENT_OFFICIAL) may log in.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__" or "st" in globals():
    show()
