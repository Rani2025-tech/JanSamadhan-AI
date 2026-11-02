import re
import secrets
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

from backend.core.messages import t, label, supported_languages
from backend.core.language import detect_language
from backend.core.understanding import understand
from backend.core.triage import triage
from backend.core.duplicates import assign_cluster
from backend.core.llm_wrapper import LLMUnavailable
from backend.db.grievances import get_grievance, create_grievance

_INDIC_DIGITS_TABLE = str.maketrans({
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9',
    '୦': '0', '୧': '1', '୨': '2', '୩': '3', '୪': '4',
    '୫': '5', '୬': '6', '୭': '7', '୮': '8', '୯': '9',
})

GREETINGS = {
    "hi", "hello", "hey", "namaste", "namaskar", "namaskaram",
    "नमस्ते", "प्रणाम", "नमस्कार", "ହଲୋ", "ନମସ୍କାର", "ଜୟ ଜଗନ୍ନାଥ",
    "good morning", "good evening", "good afternoon"
}

THANKS = {
    "thanks", "thank you", "dhanyawad", "dhanyavad",
    "धन्यवाद", "शुक्रिया", "ଧନ୍ୟବାଦ"
}

SLA_MAP = {
    "Critical": 24,
    "High": 48,
    "Medium": 168,
    "Low": 360
}

def normalize_digits(text: str) -> str:
    """Converts Devanagari and Odia numerals to standard ASCII numerals."""
    if not text:
        return ""
    return text.translate(_INDIC_DIGITS_TABLE)

def _is_greeting_or_thanks(words: list, raw_text: str) -> Optional[str]:
    """Checks if input matches greetings or thanks."""
    clean = raw_text.strip().lower()
    if clean in GREETINGS or any(w in GREETINGS for w in words):
        return "greeting"
    if clean in THANKS or any(w in THANKS for w in words):
        return "thanks"
    return None

def handle_message(text: str, state: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    """
    Main state machine for conversational civic grievance management.
    Handles Indic numerals, ticket status lookup, greetings, multi-turn location collection,
    routing, priority triage, clustering, and robust error recovery.
    """
    if state is None:
        state = {"stage": "idle", "pending": {}, "lang": "en"}
    else:
        state = dict(state)
        if "stage" not in state:
            state["stage"] = "idle"
        if "pending" not in state:
            state["pending"] = {}
        if "lang" not in state:
            state["lang"] = "en"

    raw_text = (text or "").strip()
    norm_text = normalize_digits(raw_text)
    user_lang = state.get("lang", "en")
    supported_codes = {l["code"] for l in supported_languages()}

    try:
        # a & b. Status Intent Check (GRV-1234 or GRV1234, case-insensitive)
        ticket_match = re.search(r"\bGRV-?(\d{3,})\b", norm_text, re.IGNORECASE)
        if ticket_match:
            ticket_num = ticket_match.group(1)
            ticket_id = f"GRV-{ticket_num}"
            record = get_grievance(ticket_id)
            if not record:
                reply = t("status_not_found", lang=user_lang, ticket_id=ticket_id)
                return reply, state, {"ticket_id": ticket_id, "found": False}

            rec_lang = record.get("language") or user_lang or "en"
            rec_lang = rec_lang if rec_lang in supported_codes else user_lang
            status_val = record.get("status", "Submitted")
            status_lbl = label("statuses", status_val, rec_lang)

            priority_val = record.get("priority", "Medium")
            priority_lbl = label("priorities", priority_val, rec_lang)

            updated_val = record.get("updated_at") or record.get("created_at") or ""
            sla_due = record.get("sla_due_at", "N/A")
            dept_val = record.get("department", "General")
            dept_lbl = label("departments", dept_val, rec_lang)

            lines = [
                t("status_line", lang=rec_lang, ticket_id=ticket_id, status=status_lbl, updated_at=updated_val),
                f"Department: {dept_lbl}",
                f"Priority: {priority_lbl}",
                f"SLA Due: {sla_due}"
            ]

            history = record.get("history") or []
            if history:
                lines.append("\nHistory Timeline:")
                for h in history:
                    c_time = h.get("created_at", "")
                    h_stat = h.get("status", "")
                    h_note = h.get("note", "")
                    h_actor = h.get("actor", "")
                    note_str = f" - {h_note}" if h_note else ""
                    lines.append(f"• [{c_time}] {h_stat} ({h_actor}){note_str}")

            return "\n".join(lines), state, {
                "ticket_id": ticket_id,
                "department": dept_val,
                "priority": priority_val,
                "status": status_val,
                "found": True
            }

        # c. Greeting / Thanks / Short input check (only when idle)
        words = norm_text.lower().split()
        if state.get("stage") == "idle":
            # Quick language check on initial user message
            lang_info = detect_language(raw_text, ui_lang=user_lang)
            det_code = lang_info.get("code")
            user_lang = det_code if det_code in supported_codes else user_lang
            state["lang"] = user_lang

            greet_type = _is_greeting_or_thanks(words, norm_text)
            if len(words) <= 3 and greet_type:
                return t(greet_type, lang=user_lang), state, {}

            if len(norm_text) < 8:
                return t("ask_describe", lang=user_lang), state, {}

        # d. Complaint Handling & Multi-turn Location Collection
        u = None
        current_text = raw_text

        if state.get("stage") == "awaiting_location":
            # Second message: treat as location
            pending = state.get("pending", {})
            orig_text = state.get("original_text", "")
            loc_candidate = raw_text.strip()
            loc_val = loc_candidate if len(loc_candidate) > 2 else None

            if loc_val:
                current_text = f"{orig_text} (Location: {loc_val})"
            else:
                current_text = orig_text

            pending["location"] = loc_val
            if "location" in pending.get("missing", []):
                pending["missing"].remove("location")
            if loc_val and pending.get("english_text"):
                pending["english_text"] = f"{pending['english_text']} at {loc_val}"

            u = pending
            user_lang = state.get("lang", "en")
            state["stage"] = "idle"
            state["pending"] = {}
        else:
            # First complaint message: understand()
            try:
                u = understand(raw_text, ui_lang=user_lang)
            except LLMUnavailable:
                u = {
                    "language": user_lang,
                    "english_text": raw_text,
                    "category": "Other / Needs Review",
                    "location": None,
                    "summary": raw_text[:150],
                    "missing": [],
                    "used_llm": False,
                    "needs_review": True
                }

            u_lang = u.get("language")
            user_lang = u_lang if u_lang in supported_codes else user_lang
            state["lang"] = user_lang

            # If location is missing and complaint is under initial review, ask once
            if "location" in u.get("missing", []) and not u.get("location"):
                state["stage"] = "awaiting_location"
                state["pending"] = u
                state["original_text"] = raw_text
                return t("ask_location", lang=user_lang), state, {
                    "stage": "awaiting_location",
                    "needs_location": True
                }

        # e. Triage -> Create Grievance -> Assign Cluster
        try:
            tr = triage(u, original_text=current_text)
        except LLMUnavailable:
            tr = {
                "department": "Municipal Corporation - Solid Waste",
                "category": "Other / Needs Review",
                "confidence": 0.40,
                "routing_reason": "LLM unavailable zero-network fallback",
                "priority": "Medium",
                "priority_reason": "Default fallback priority",
                "needs_review": True
            }

        priority = tr.get("priority", "Medium")
        needs_review = bool(tr.get("needs_review") or u.get("needs_review"))

        # Generate secure random 6-digit PIN for citizen tracking privacy
        pin = f"{secrets.randbelow(900000) + 100000}"

        grv_data = {
            "citizen_name": "Citizen",
            "original_text": current_text,
            "language": u.get("language", user_lang),
            "translated_text": u.get("english_text", current_text),
            "summary": u.get("summary") or u.get("english_text", current_text)[:150],
            "location": u.get("location"),
            "area": u.get("location") or "General Area",
            "department": tr.get("department"),
            "category": tr.get("category"),
            "confidence": tr.get("confidence", 0.5),
            "routing_reason": tr.get("routing_reason", ""),
            "priority": priority,
            "priority_reason": tr.get("priority_reason", ""),
            "needs_review": 1 if needs_review else 0,
            "status": "Submitted",
            "pin": pin
        }

        # Optional contact extraction from state
        contact_raw = state.get("contact")
        if contact_raw:
            c_str = re.sub(r"[\s\-]", "", str(contact_raw).strip())
            if c_str.startswith("+91"):
                c_str = c_str[3:]
            elif c_str.startswith("91") and len(c_str) == 12:
                c_str = c_str[2:]
            elif c_str.startswith("0") and len(c_str) == 11:
                c_str = c_str[1:]
            if re.fullmatch(r"[6-9]\d{9}", c_str):
                grv_data["contact"] = c_str

        ticket_id = create_grievance(grv_data)
        record = get_grievance(ticket_id)
        sla_due_at = record.get("sla_due_at", "") if record else ""
        sla_hours = SLA_MAP.get(priority, 168)

        # Cluster assignment
        cluster_info = assign_cluster(
            ticket_id=ticket_id,
            english_text=u.get("english_text", current_text),
            category=tr.get("category"),
            department=tr.get("department"),
            location=u.get("location")
        )

        # Construct reply
        p_label = label("priorities", priority, user_lang)
        dept_name = tr.get("department", "General")
        dept_label = label("departments", dept_name, user_lang)

        reply_sections = [
            t("ticket_created", lang=user_lang, ticket_id=ticket_id, pin=pin, department=dept_label, priority=p_label),
            t("sla_notice", lang=user_lang, sla_hours=sla_hours, sla_due_at=sla_due_at)
        ]

        if needs_review:
            reply_sections.append(t("review_note", lang=user_lang))

        if cluster_info:
            count = cluster_info.get("report_count", 2)
            reply_sections.append(t("cluster_notice", lang=user_lang, count=count))

        reply_text = "\n\n".join(reply_sections)

        meta = {
            "ticket_id": ticket_id,
            "pin": pin,
            "department": tr.get("department"),
            "category": tr.get("category"),
            "location": u.get("location"),
            "summary": grv_data["summary"],
            "priority": priority,
            "confidence": tr.get("confidence"),
            "sla_due_at": sla_due_at,
            "cluster": cluster_info,
            "needs_review": needs_review
        }

        return reply_text, state, meta

    except Exception as e:
        state["stage"] = "idle"
        state["pending"] = {}
        err_reply = t("generic_error", lang=user_lang)
        return err_reply, state, {"error": str(e)}

