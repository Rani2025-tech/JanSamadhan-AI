import os
import time
from typing import Optional, Dict, Any, List
import requests
import streamlit as st

from ui_text import ui

class ApiError(Exception):
    """Custom exception for clean user-facing API failure reporting."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def _get_base_url() -> str:
    raw = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
    if raw.endswith("/api"):
        return raw
    return f"{raw}/api"

@st.cache_resource
def get_session() -> requests.Session:
    """Provides a thread-safe persistent HTTP session for frontend requests."""
    return requests.Session()

def _handle_unauthorized(resp: requests.Response) -> None:
    if resp.status_code == 401:
        try:
            from auth_helpers import clear_staff_session
            clear_staff_session()
        except Exception:
            pass
        raise ApiError("Staff session expired or unauthorized. Please log in again.", status_code=401)

def _request_with_retry(method: str, url: str, **kwargs) -> requests.Response:
    kwargs.setdefault("timeout", 25)
    session = get_session()
    last_err = None
    for attempt in range(2):
        try:
            resp = session.request(method, url, **kwargs)
            if resp.status_code in (502, 503) and attempt == 0:
                time.sleep(1.0)
                continue
            return resp
        except (requests.ConnectionError, requests.Timeout) as e:
            last_err = e
            if attempt == 0:
                time.sleep(1.0)
                continue
            raise ApiError(f"Connection to server failed. Please ensure backend service is running.")
    raise ApiError(f"Server is temporarily unavailable (status code {getattr(last_err, 'response', None)}).")

def warmup(lang: str = "en") -> None:
    """Pings /api/health once per user session to avoid cold-start delays."""
    if st.session_state.get("warmed_up"):
        return
    base = _get_base_url()
    try:
        session = get_session()
        session.get(f"{base}/health", timeout=6)
    except Exception:
        pass
    st.session_state["warmed_up"] = True

def chat(message: str, state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Sends a citizen chat message and state machine context to /api/grievances/chat."""
    base = _get_base_url()
    url = f"{base}/grievances/chat"
    payload = {"message": message, "state": state or {}}
    resp = _request_with_retry("POST", url, json=payload)
    if resp.status_code == 429:
        raise ApiError("Too many messages, please wait a minute before sending another message.", status_code=429)
    if resp.status_code != 200:
        detail = resp.json().get("detail", "Error processing message") if resp.headers.get("content-type") == "application/json" else resp.text
        raise ApiError(f"Chat failed: {detail}", status_code=resp.status_code)
    return resp.json()

def private_ticket(ticket_id: str, pin: str) -> Dict[str, Any]:
    """Unlocks full private citizen grievance details using the 6-digit tracking PIN."""
    base = _get_base_url()
    url = f"{base}/grievances/{ticket_id}/private"
    payload = {"pin": str(pin).strip()}
    resp = _request_with_retry("POST", url, json=payload)
    if resp.status_code == 403:
        raise ApiError("The ticket ID or tracking PIN is not correct.", status_code=403)
    if resp.status_code == 429:
        retry_after = resp.headers.get("retry-after") or resp.headers.get("Retry-After")
        if retry_after:
            raise ApiError(f"Too many attempts. Please try again after {retry_after} seconds.", status_code=429)
        raise ApiError("Too many attempts, please try again in a few minutes.", status_code=429)
    if resp.status_code != 200:
        detail = resp.json().get("detail", "Error unlocking ticket") if resp.headers.get("content-type") == "application/json" else resp.text
        raise ApiError(f"Failed to unlock details: {detail}", status_code=resp.status_code)
    return resp.json()

def get_ticket(ticket_id: str, token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves grievance details and history from /api/grievances/{ticket_id}."""
    base = _get_base_url()
    url = f"{base}/grievances/{ticket_id}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = _request_with_retry("GET", url, headers=headers)
    if token:
        _handle_unauthorized(resp)
    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        raise ApiError(f"Failed to fetch ticket: {resp.text}", status_code=resp.status_code)
    return resp.json()

def send_feedback(ticket_id: str, rating: int, comment: str = "") -> Dict[str, Any]:
    """Submits 1-5 star citizen rating to /api/grievances/{ticket_id}/feedback."""
    base = _get_base_url()
    url = f"{base}/grievances/{ticket_id}/feedback"
    payload = {"rating": rating, "comment": comment}
    resp = _request_with_retry("POST", url, json=payload)
    if resp.status_code != 200:
        raise ApiError(f"Failed to submit feedback: {resp.text}", status_code=resp.status_code)
    return resp.json()

def get_public_stats() -> Dict[str, Any]:
    """Retrieves aggregated public metrics from /api/grievances/public-stats."""
    base = _get_base_url()
    url = f"{base}/grievances/public-stats"
    resp = _request_with_retry("GET", url)
    if resp.status_code != 200:
        raise ApiError(f"Failed to fetch public stats: {resp.text}", status_code=resp.status_code)
    return resp.json()

def login(email: str, password: str) -> Dict[str, Any]:
    """
    Authenticates municipal staff member via POST /api/auth/login.
    Returns: {token, role, name, department, expires_in}
    Errors: 401 generic message, 429 with retry-after.
    """
    base = _get_base_url()
    url = f"{base}/auth/login"
    payload = {"email": email.strip(), "password": password}
    resp = _request_with_retry("POST", url, json=payload)
    if resp.status_code == 401:
        raise ApiError("Invalid email or password.", status_code=401)
    if resp.status_code == 429:
        retry_after = resp.headers.get("retry-after") or resp.headers.get("Retry-After")
        if retry_after:
            raise ApiError(f"Too many login attempts. Please try again after {retry_after} seconds.", status_code=429)
        raise ApiError("Too many login attempts. Please try again in a few minutes.", status_code=429)
    if resp.status_code != 200:
        detail = resp.json().get("detail", "Login failed") if resp.headers.get("content-type") == "application/json" else resp.text
        raise ApiError(f"Login failed: {detail}", status_code=resp.status_code)
    return resp.json()

def demo_login(role: str) -> Dict[str, Any]:
    """
    One-click demo login for judges via POST /api/auth/demo-login.
    Role: 'official' or 'admin'.
    Returns: {token, role, name, department, expires_in, demo: True}
    Errors: 404 mapped to 'Demo mode is not enabled on this server.',
            429 mapped to rate-limit message with Retry-After if present.
    """
    base = _get_base_url()
    url = f"{base}/auth/demo-login"
    payload = {"role": role.strip().lower()}
    resp = _request_with_retry("POST", url, json=payload)
    if resp.status_code == 404:
        raise ApiError("Demo mode is not enabled on this server.", status_code=404)
    if resp.status_code == 429:
        retry_after = resp.headers.get("retry-after") or resp.headers.get("Retry-After")
        if retry_after:
            raise ApiError(f"Too many demo login requests. Please try again after {retry_after} seconds.", status_code=429)
        raise ApiError("Too many demo login requests. Please try again in a few minutes.", status_code=429)
    if resp.status_code != 200:
        detail = resp.json().get("detail", "Demo login failed") if resp.headers.get("content-type") == "application/json" else resp.text
        raise ApiError(f"Demo login failed: {detail}", status_code=resp.status_code)
    return resp.json()

# ── Admin API Helpers ──────────────────────────────────────────

def list_grievances(token: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Admin-only: lists grievances with optional status/dept/priority filters."""
    base = _get_base_url()
    url = f"{base}/grievances/"
    headers = {"Authorization": f"Bearer {token}"}
    params = filters or {}
    resp = _request_with_retry("GET", url, headers=headers, params=params)
    _handle_unauthorized(resp)
    if resp.status_code != 200:
        raise ApiError(f"Failed to load grievances: {resp.text}", status_code=resp.status_code)
    return resp.json()

def update_status(token: str, ticket_id: str, status: str, note: str = "") -> Dict[str, Any]:
    """Staff/Admin: updates ticket status and appends timeline note."""
    base = _get_base_url()
    url = f"{base}/grievances/{ticket_id}/status"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"status": status, "note": note}
    resp = _request_with_retry("PATCH", url, headers=headers, json=payload)
    _handle_unauthorized(resp)
    if resp.status_code != 200:
        detail = resp.json().get("detail", resp.text) if resp.headers.get("content-type") == "application/json" else resp.text
        raise ApiError(f"Failed to update status: {detail}", status_code=resp.status_code)
    return resp.json()

def admin_stats(token: str) -> Dict[str, Any]:
    """Admin-only: retrieves dashboard statistics and metrics."""
    base = _get_base_url()
    url = f"{base}/grievances/admin/stats"
    headers = {"Authorization": f"Bearer {token}"}
    resp = _request_with_retry("GET", url, headers=headers)
    _handle_unauthorized(resp)
    if resp.status_code != 200:
        raise ApiError(f"Failed to load statistics: {resp.text}", status_code=resp.status_code)
    return resp.json()

def admin_clusters(token: str) -> List[Dict[str, Any]]:
    """Admin-only: retrieves cluster listing for deduplication review."""
    base = _get_base_url()
    url = f"{base}/grievances/admin/clusters"
    headers = {"Authorization": f"Bearer {token}"}
    resp = _request_with_retry("GET", url, headers=headers)
    _handle_unauthorized(resp)
    if resp.status_code != 200:
        raise ApiError(f"Failed to load clusters: {resp.text}", status_code=resp.status_code)
    return resp.json()

def flag_misrouted(token: str, ticket_id: str, note: str) -> Dict[str, Any]:
    """Flags a grievance as misrouted so an administrator can re-route it."""
    base = _get_base_url()
    url = f"{base}/grievances/{ticket_id}/flag-misrouted"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"note": note}
    resp = _request_with_retry("POST", url, headers=headers, json=payload)
    _handle_unauthorized(resp)
    if resp.status_code != 200:
        detail = resp.json().get("detail", resp.text) if resp.headers.get("content-type") == "application/json" else resp.text
        raise ApiError(f"Failed to flag misrouted ticket: {detail}", status_code=resp.status_code)
    return resp.json()

def reroute(token: str, ticket_id: str, department: str, category: str, note: str) -> Dict[str, Any]:
    """Admin-only: re-routes a grievance to the correct department and category."""
    base = _get_base_url()
    url = f"{base}/grievances/{ticket_id}/routing"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"department": department, "category": category, "note": note}
    resp = _request_with_retry("PATCH", url, headers=headers, json=payload)
    _handle_unauthorized(resp)
    if resp.status_code != 200:
        detail = resp.json().get("detail", resp.text) if resp.headers.get("content-type") == "application/json" else resp.text
        raise ApiError(f"Failed to re-route ticket: {detail}", status_code=resp.status_code)
    return resp.json()
