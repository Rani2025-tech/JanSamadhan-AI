"""
Pure helper functions for JanSamadhan municipal staff and admin workbench.
No Streamlit dependencies - safe for unit testing.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Any, List, Dict

# Indian Standard Time (UTC+05:30)
IST = timezone(timedelta(hours=5, minutes=30))

# Note on database timestamps:
# In backend/db/grievances.py, created_at, updated_at, and sla_due_at timestamps are stored
# as naive UTC strings formatted as "%Y-%m-%d %H:%M:%S" generated via datetime.utcnow().
# Therefore, any naive datetime or unadorned timestamp string parsed without offset
# must be treated as UTC before converting to IST.

def _parse_to_utc(ts: Any) -> Optional[datetime]:
    """Parse various timestamp representations into an aware UTC datetime."""
    if ts is None:
        return None
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    
    s = str(ts).strip()
    if not s or s.lower() in ("none", "null", "-", ""):
        return None

    # Replace Z with +00:00 for ISO parsing
    s_iso = s.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s_iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except Exception:
            pass

    return None

def format_ist(ts: Any) -> str:
    """
    Format a timestamp into 'DD Mon YYYY, HH:MM' in Indian Standard Time (IST).
    Returns '-' for None, empty, or unparseable inputs.
    """
    dt_utc = _parse_to_utc(ts)
    if dt_utc is None:
        return "-"
    dt_ist = dt_utc.astimezone(IST)
    return dt_ist.strftime("%d %b %Y, %H:%M")

def sla_label(sla_due_at: Any, status: Optional[str], now: Optional[Any] = None) -> str:
    """
    Computes human-friendly SLA status label:
    - 'Resolved' when ticket is marked Resolved
    - 'Due in 5h 20m' / 'Due in 2d 3h' when open
    - 'Overdue by 4h' / 'Overdue by 1d 6h' when past due
    - '-' when sla_due_at is missing/invalid
    """
    if status and str(status).strip().lower() == "resolved":
        return "Resolved"

    dt_due = _parse_to_utc(sla_due_at)
    if dt_due is None:
        return "-"

    if now is None:
        dt_now = datetime.now(timezone.utc)
    else:
        dt_now = _parse_to_utc(now)
        if dt_now is None:
            dt_now = datetime.now(timezone.utc)

    diff = dt_due - dt_now
    total_seconds = diff.total_seconds()

    if total_seconds >= 0:
        # Open / Due in future
        secs = int(total_seconds)
        days = secs // 86400
        rem = secs % 86400
        hours = rem // 3600
        minutes = (rem % 3600) // 60
        if days >= 1:
            return f"Due in {days}d {hours}h"
        return f"Due in {hours}h {minutes}m"
    else:
        # Overdue
        secs = int(abs(total_seconds))
        days = secs // 86400
        rem = secs % 86400
        hours = rem // 3600
        if days >= 1:
            return f"Overdue by {days}d {hours}h"
        return f"Overdue by {hours}h"

def allowed_next_statuses(current: Optional[str]) -> List[str]:
    """
    Returns valid next status transitions strictly following municipal workflow:
    - Submitted -> ['Assigned']
    - Assigned -> ['In Progress']
    - In Progress -> ['Resolved']
    - Reopened -> ['Assigned', 'In Progress']
    - Resolved -> []
    """
    if not current:
        return []

    c = str(current).strip().lower()
    if c == "submitted":
        return ["Assigned"]
    elif c == "assigned":
        return ["In Progress"]
    elif c == "in progress":
        return ["Resolved"]
    elif c == "reopened":
        return ["Assigned", "In Progress"]
    elif c == "resolved":
        return []
    return []

def build_filters(**kwargs) -> Dict[str, Any]:
    """
    Builds clean backend query parameters dict:
    - Drops None, empty strings, and 'All' / 'Any'
    - Maps boolean flags (overdue_only -> overdue, needs_review_only -> needs_review)
    """
    filters = {}
    for key, val in kwargs.items():
        if val is None:
            continue
        if isinstance(val, str):
            v = val.strip()
            if not v or v.lower() in ("all", "any", "none"):
                continue
            filters[key] = v
        elif isinstance(val, bool):
            if val:
                if key in ("overdue_only", "overdue"):
                    filters["overdue"] = True
                elif key in ("needs_review_only", "needs_review"):
                    filters["needs_review"] = True
                else:
                    filters[key] = True
        elif isinstance(val, (int, float)):
            filters[key] = val
    return filters

