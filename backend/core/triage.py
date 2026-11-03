from typing import Dict, Any
from backend.core.router import route
from backend.core.priority import score_priority

def triage(understood: Dict[str, Any], original_text: str = "") -> Dict[str, Any]:
    """
    Orchestrates routing, priority scoring, and review flagging into a unified payload
    ready for database grievance creation.
    """
    routed = route(understood)
    category = routed["category"]
    department = routed["department"]

    english_text = understood.get("english_text", "")
    prio = score_priority(english_text, category, original_text)

    needs_review = int(bool(routed["needs_review"] or understood.get("needs_review", False)))

    return {
        "department": department,
        "category": category,
        "confidence": routed["confidence"],
        "routing_reason": routed["reason"],
        "priority": prio["priority"],
        "priority_reason": prio["reason"],
        "needs_review": needs_review
    }

