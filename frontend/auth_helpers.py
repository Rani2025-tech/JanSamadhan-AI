import time
import re
from typing import Optional, Dict, Any

def valid_mobile(text: Optional[str]) -> Optional[str]:
    """
    Validates and normalizes an Indian 10-digit mobile number:
    - Accepts spaces, dashes, +91 prefix, leading 0
    - Must start with digits 6, 7, 8, or 9
    - Returns normalized 10-digit string, or None if invalid.
    """
    if not text:
        return None
    raw = str(text).strip()
    cleaned = re.sub(r"[\s\-\(\)\.]", "", raw)
    if cleaned.startswith("+91"):
        cleaned = cleaned[3:]
    elif cleaned.startswith("0") and len(cleaned) == 11:
        cleaned = cleaned[1:]

    if len(cleaned) == 10 and cleaned.isdigit() and cleaned[0] in "6789":
        return cleaned
    return None

def role_allowed(selected_tab: Optional[str], server_role: Optional[str]) -> bool:
    """
    Checks if the selected login tab matches the authorized role returned by the server:
    Tabs: 'citizen' -> CITIZEN, 'official' -> DEPARTMENT_OFFICIAL, 'admin' -> ADMIN.
    Tolerates case differences, spaces, and display labels.
    """
    if not selected_tab or not server_role:
        return False

    tab_str = str(selected_tab).strip().lower()
    role_str = str(server_role).strip().upper()

    tab_to_role = {
        "citizen": "CITIZEN",
        "official": "DEPARTMENT_OFFICIAL",
        "department official": "DEPARTMENT_OFFICIAL",
        "department_official": "DEPARTMENT_OFFICIAL",
        "admin": "ADMIN",
        "administrator": "ADMIN"
    }

    expected_role = tab_to_role.get(tab_str)
    if not expected_role:
        return False

    return expected_role == role_str

def is_staff_session_valid(session: Optional[Any] = None) -> bool:
    """
    Checks if an active staff session exists in session_state, has an authorized role
    (ADMIN or DEPARTMENT_OFFICIAL), and token has not expired.
    Clears the session if expired or unauthorized.
    """
    if session is None:
        try:
            import streamlit as st
            session = st.session_state
        except Exception:
            return False

    token = session.get("token")
    role = session.get("role")
    expires_at = session.get("token_expires_at")

    if not token or not role or expires_at is None:
        return False

    if str(role).upper() not in ("ADMIN", "DEPARTMENT_OFFICIAL"):
        clear_staff_session(session)
        return False

    try:
        now = time.time()
        if now >= float(expires_at):
            clear_staff_session(session)
            return False
    except (ValueError, TypeError):
        clear_staff_session(session)
        return False

    return True

def set_staff_session(login_data: Dict[str, Any], session: Optional[Any] = None) -> None:
    """
    Stores authenticated staff credentials, role, department, and token expiry in session_state.
    Fields stored: token, role, staff_name, department, token_expires_at.
    """
    if session is None:
        try:
            import streamlit as st
            session = st.session_state
        except Exception:
            return

    now = time.time()
    expires_in = float(login_data.get("expires_in", 86400))
    session["token"] = login_data.get("token", "")
    session["admin_token"] = login_data.get("token", "")
    session["role"] = str(login_data.get("role", "")).upper()
    session["staff_name"] = login_data.get("name") or "Staff"
    session["department"] = login_data.get("department")
    session["token_expires_at"] = now + expires_in
    session["staff_demo"] = bool(login_data.get("demo"))
    session["user"] = {
        "id": login_data.get("name") or "staff",
        "name": login_data.get("name") or "Staff",
        "role": session["role"],
        "department": session["department"]
    }

def clear_staff_session(session: Optional[Any] = None) -> None:
    """
    Clears all staff credentials and cached private citizen data upon logout or token expiry.
    Clears: token, role, staff_name, department, token_expires_at,
    unlocked_tickets, unlocked_pins, last_pin.
    """
    if session is None:
        try:
            import streamlit as st
            session = st.session_state
        except Exception:
            return

    keys_to_clear = [
        "token", "admin_token", "role", "staff_name", "department",
        "token_expires_at", "user", "staff_demo",
        "unlocked_tickets", "unlocked_pins", "last_pin"
    ]
    for key in keys_to_clear:
        if key in session:
            try:
                del session[key]
            except Exception:
                session[key] = None

