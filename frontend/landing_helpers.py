from typing import Optional, Dict, Any
from auth_helpers import (
    is_staff_session_valid,
    clear_staff_session,
    set_staff_session,
    valid_mobile,
    role_allowed
)

def format_resolution_time(hours: Optional[float]) -> str:
    """
    Formats average resolution time according to SLA guidelines:
    - null/None: "N/A"
    - below 48 hours: in hours (e.g. "12 hrs" or "24 hrs")
    - from 48 hours up: in days with 1 decimal place (e.g. "2.0 days", "2.5 days")
    """
    if hours is None:
        return "N/A"
    try:
        val = float(hours)
    except (ValueError, TypeError):
        return "N/A"

    if val < 48:
        rounded_hrs = round(val)
        return f"{rounded_hrs} hr" if rounded_hrs == 1 else f"{rounded_hrs} hrs"
    days = val / 24.0
    return f"{days:.1f} days"

def format_public_stats(stats: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Formats raw /api/grievances/public-stats dictionary for user display:
    - computes avg_resolution_str using format_resolution_time
    - provides demo_label ("Demo data" when demo is True)
    """
    if not stats:
        return {
            "total": 0,
            "resolved": 0,
            "open": 0,
            "avg_resolution_str": "N/A",
            "overdue_count": 0,
            "demo": False,
            "demo_label": ""
        }
    avg_hrs = stats.get("avg_resolution_hours")
    is_demo = bool(stats.get("demo", False))
    return {
        "total": int(stats.get("total", 0)),
        "resolved": int(stats.get("resolved", 0)),
        "open": int(stats.get("open", 0)),
        "avg_resolution_str": format_resolution_time(avg_hrs),
        "overdue_count": int(stats.get("overdue_count", 0)),
        "demo": is_demo,
        "demo_label": "Demo data" if is_demo else ""
    }

