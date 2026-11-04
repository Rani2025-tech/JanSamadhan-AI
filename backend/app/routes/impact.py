import json
from pathlib import Path
from collections import Counter, defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Complaint

impact_router = APIRouter(tags=["Impact"])

# Load shared national locations list
LOCATIONS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "india_locations.json"
ALL_STATES = []
if LOCATIONS_FILE.exists():
    try:
        with open(LOCATIONS_FILE, "r", encoding="utf-8") as f:
            loc_data = json.load(f)
            ALL_STATES = sorted(list(loc_data.keys()))
    except Exception:
        ALL_STATES = []

@impact_router.get("/impact/states")
def get_impact_states(db: Session = Depends(get_db)):
    """
    Returns complaints grouped by state (and districts underneath) with total, open, resolved,
    and top category, computed directly from live DB records.
    """
    complaints = db.query(Complaint).all()
    
    state_map = defaultdict(lambda: {
        "total": 0,
        "open": 0,
        "resolved": 0,
        "categories": Counter(),
        "districts": defaultdict(lambda: {
            "total": 0,
            "open": 0,
            "resolved": 0,
            "categories": Counter()
        })
    })

    for c in complaints:
        st = c.state or "Odisha"
        dist = c.district or "Unknown"
        is_resolved = (c.status or "").lower() == "resolved"

        state_map[st]["total"] += 1
        if is_resolved:
            state_map[st]["resolved"] += 1
        else:
            state_map[st]["open"] += 1
        if c.category:
            state_map[st]["categories"][c.category] += 1

        state_map[st]["districts"][dist]["total"] += 1
        if is_resolved:
            state_map[st]["districts"][dist]["resolved"] += 1
        else:
            state_map[st]["districts"][dist]["open"] += 1
        if c.category:
            state_map[st]["districts"][dist]["categories"][c.category] += 1

    states_result = []
    for st, data in state_map.items():
        top_cat = data["categories"].most_common(1)[0][0] if data["categories"] else "General"
        district_list = []
        for d_name, d_data in data["districts"].items():
            d_top_cat = d_data["categories"].most_common(1)[0][0] if d_data["categories"] else "General"
            district_list.append({
                "district": d_name,
                "total": d_data["total"],
                "open": d_data["open"],
                "resolved": d_data["resolved"],
                "top_category": d_top_cat
            })
        district_list.sort(key=lambda x: x["total"], reverse=True)

        states_result.append({
            "state": st,
            "total": data["total"],
            "open": data["open"],
            "resolved": data["resolved"],
            "top_category": top_cat,
            "districts": district_list
        })

    # Sort states by total volume descending
    states_result.sort(key=lambda x: x["total"], reverse=True)

    return {
        "states": states_result,
        "all_states": ALL_STATES,
        "total_states_active": len(states_result),
        "total_complaints": len(complaints)
    }

