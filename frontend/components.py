import re
import html
from typing import Optional, Dict, Any, List
from ui_text import ui, label

_DIGIT_MAP = str.maketrans({
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9',
    '୦': '0', '୧': '1', '୨': '2', '୩': '3', '୪': '4',
    '୫': '5', '୬': '6', '୭': '7', '୮': '8', '୯': '9',
})

def esc(value: Any) -> str:
    """Escapes HTML entities to protect against XSS injections."""
    if value is None:
        return ""
    return html.escape(str(value))

def normalize_ticket_id(text: Optional[str]) -> Optional[str]:
    """
    Normalizes user ticket input:
    Strips whitespace, converts Devanagari/Odia numerals to ASCII,
    accepts 'GRV1042' or 'grv-1042', returns 'GRV-1042' or None.
    """
    if not text:
        return None
    cleaned = str(text).strip().translate(_DIGIT_MAP).upper()
    match = re.search(r"\bGRV[-\s]?(\d{3,})\b", cleaned)
    if match:
        return f"GRV-{match.group(1)}"
    match_exact = re.match(r"^GRV[-\s]?(\d{3,})$", cleaned)
    if match_exact:
        return f"GRV-{match_exact.group(1)}"
    return None

def normalize_pin(text: Optional[str]) -> Optional[str]:
    """
    Normalizes 6-digit citizen tracking PIN:
    Converts Devanagari/Odia digits, strips all whitespace,
    and returns an exact 6-digit ASCII string, or None if invalid.
    """
    if not text:
        return None
    cleaned = re.sub(r"\s+", "", str(text)).translate(_DIGIT_MAP)
    if re.fullmatch(r"\d{6}", cleaned):
        return cleaned
    return None

def overdue_chip(lang: str = "en") -> str:
    """Renders small badge indicating SLA overdue status."""
    lbl = esc(ui("overdue", lang))
    return f'<span class="chip" style="background: #FFE6E6; color: #C5221F; font-weight: 600; border: 1px solid #F5C6CB;">⚠️ {lbl}</span>'

def escalation_chip(level: int, lang: str = "en") -> str:
    """Renders small badge indicating SLA breach escalation level."""
    lbl = esc(ui("escalated", lang))
    return f'<span class="chip" style="background: #FFF3CD; color: #856404; font-weight: 600; border: 1px solid #FFEEBA;">⚡ {lbl} L{level}</span>'

def priority_chip(priority: Optional[str], lang: str = "en") -> str:
    """Renders HTML priority badge styled with low/med/high/critical palettes."""
    p_raw = (priority or "Medium").capitalize()
    p_text = esc(label("priorities", p_raw, lang))
    chip_class = f"chip chip-{p_raw.lower()}"
    return f'<span class="{chip_class}">{p_text}</span>'

def status_pill(status: Optional[str], lang: str = "en") -> str:
    """Renders HTML status indicator with status-pill and badge-dot."""
    s_raw = status or "Submitted"
    s_text = esc(label("statuses", s_raw, lang))
    return f'<span class="status-pill"><span class="badge-dot"></span>{s_text}</span>'

def stepper(status: Optional[str], history: Optional[List[Dict[str, Any]]] = None, lang: str = "en") -> str:
    """
    Renders 4-step progression stepper:
    Submitted -> Assigned -> In Progress -> Resolved.
    Reopened displays as In Progress with a highlight note.
    """
    steps = ["Submitted", "Assigned", "In Progress", "Resolved"]
    stat_clean = (status or "Submitted").strip()
    is_reopened = stat_clean.lower() == "reopened"

    if is_reopened or stat_clean.lower() == "in progress":
        curr_idx = 2
    elif stat_clean.lower() == "resolved":
        curr_idx = 3
    elif stat_clean.lower() == "assigned":
        curr_idx = 1
    else:
        curr_idx = 0

    # Extract latest timestamps from history
    hist_times: Dict[str, str] = {}
    if history and isinstance(history, list):
        for h in history:
            h_stat = h.get("status")
            h_time = h.get("created_at")
            if h_stat and h_time:
                hist_times[h_stat] = str(h_time)

    step_items_html = []
    for idx, s_name in enumerate(steps):
        if idx < curr_idx:
            step_state_cls = "step-done"
            badge_icon = "✓"
        elif idx == curr_idx:
            step_state_cls = "step-current"
            badge_icon = str(idx + 1)
        else:
            step_state_cls = "step-pending"
            badge_icon = str(idx + 1)

        title_text = esc(label("statuses", s_name, lang))
        time_text = esc(hist_times.get(s_name, ""))

        time_html = f'<div class="step-time">{time_text}</div>' if time_text else ''
        step_items_html.append(f"""
        <div class="step {step_state_cls}">
            <div class="step-circle">{badge_icon}</div>
            <div class="step-title">{title_text}</div>
            {time_html}
        </div>
        """)

    reopened_html = ""
    if is_reopened:
        reopened_html = f'<div class="small-note" style="color: var(--badge); font-weight: 600; text-align: center; margin-top: 8px;">• {esc(ui("reopened_note", lang))}</div>'

    return f"""
    <div style="margin: 1.25rem 0;">
        <div class="stepper">
            {"".join(step_items_html)}
        </div>
        {reopened_html}
    </div>
    """

def understanding_card(ticket: Dict[str, Any], lang: str = "en") -> str:
    """
    Renders 3-column Category / Location / Summary card with forward routing note
    and tracking ID chip.
    """
    tid = esc(ticket.get("ticket_id", ""))
    cat_val = ticket.get("category") or ""
    cat = esc(label("categories", cat_val, lang) if cat_val else ui("category", lang))
    loc = esc(ticket.get("location") or ticket.get("area") or "Not specified")
    summary = esc(ticket.get("summary") or ticket.get("english_text") or ticket.get("original_text", ""))
    dept_val = ticket.get("department", "General Administration")
    dept = esc(label("departments", dept_val, lang))
    conf_pct = round(float(ticket.get("confidence", 0.95)) * 100)
    fwd_line = esc(ui("forward_line", lang, department=dept, confidence=conf_pct))
    priority_html = priority_chip(ticket.get("priority"), lang)
    eng_note = esc(ui("english_note", lang))

    return f"""
    <div class="ticket-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span class="id-chip">{tid}</span>
            {priority_html}
        </div>
        <div class="understanding">
            <div class="understanding-item">
                <span class="understanding-label">{esc(ui('category', lang))}</span>
                <span class="understanding-val">{cat}</span>
            </div>
            <div class="understanding-item">
                <span class="understanding-label">{esc(ui('location', lang))}</span>
                <span class="understanding-val">{loc}</span>
            </div>
            <div class="understanding-item">
                <span class="understanding-label">{esc(ui('summary_title', lang))} <small style="font-weight:normal;opacity:0.8;">{eng_note}</small></span>
                <span class="understanding-val">{summary}</span>
            </div>
        </div>
        <div class="small-note" style="margin-top: 6px;">
            {fwd_line}
        </div>
    </div>
    """

def understanding_card_from_meta(meta: Dict[str, Any], lang: str = "en") -> str:
    """
    Builds the Category / Location / Summary block, the forwarded-to line with confidence
    and the tracking ID chip purely from chat meta (no extra request), escaping every value.
    """
    tid = esc(meta.get("ticket_id", ""))
    cat_val = meta.get("category") or ""
    cat = esc(label("categories", cat_val, lang) if cat_val else ui("category", lang))
    loc = esc(meta.get("location") or "Not specified")
    summary = esc(meta.get("summary", ""))
    dept_val = meta.get("department", "General Administration")
    dept = esc(label("departments", dept_val, lang))
    conf_val = meta.get("confidence")
    conf_pct = round(float(conf_val if conf_val is not None else 0.95) * 100)
    fwd_line = esc(ui("forward_line", lang, department=dept, confidence=conf_pct))
    priority_html = priority_chip(meta.get("priority"), lang)
    eng_note = esc(ui("english_note", lang))

    return f"""
    <div class="ticket-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span class="id-chip">{tid}</span>
            {priority_html}
        </div>
        <div class="understanding">
            <div class="understanding-item">
                <span class="understanding-label">{esc(ui('category', lang))}</span>
                <span class="understanding-val">{cat}</span>
            </div>
            <div class="understanding-item">
                <span class="understanding-label">{esc(ui('location', lang))}</span>
                <span class="understanding-val">{loc}</span>
            </div>
            <div class="understanding-item">
                <span class="understanding-label">{esc(ui('summary_title', lang))} <small style="font-weight:normal;opacity:0.8;">{eng_note}</small></span>
                <span class="understanding-val">{summary}</span>
            </div>
        </div>
        <div class="small-note" style="margin-top: 6px;">
            {fwd_line}
        </div>
    </div>
    """

def pin_notice(pin: str, ticket_id: str, lang: str = "en") -> str:
    """
    Renders highlighted card displaying the 6-digit citizen tracking PIN.
    Reminds citizen that it is shown only once and needed to view complaint details.
    """
    esc_pin = esc(pin)
    esc_tid = esc(ticket_id)
    title = esc(ui("pin_title", lang))
    body = esc(ui("pin_notice_body", lang))
    return f"""
    <div style="background: linear-gradient(135deg, rgba(138, 42, 150, 0.08) 0%, rgba(249, 202, 220, 0.25) 100%);
                border: 2px dashed var(--primary); border-radius: var(--radius-md); padding: 14px 18px; margin: 12px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
            <div style="font-weight: 700; color: var(--primary); font-size: 15px;">
                🔑 {title} ({esc_tid})
            </div>
            <div class="pin-code" style="font-size: 20px; font-weight: 800; letter-spacing: 4px; color: var(--primary-dark);
                        background: #FFFFFF; padding: 4px 14px; border-radius: var(--radius-sm); border: 1px solid var(--border);">
                {esc_pin}
            </div>
        </div>
        <p style="margin: 8px 0 0 0; font-size: 13px; color: var(--text); line-height: 1.4;">
            {body}
        </p>
    </div>
    """

def ticket_card(ticket: Dict[str, Any], lang: str = "en") -> str:
    """
    Renders grievance card tolerating public shapes (omitted summary/location)
    and highlighting overdue or escalation level chips.
    """
    tid = esc(ticket.get("ticket_id", ""))
    status_html = status_pill(ticket.get("status"), lang)
    p_chip = priority_chip(ticket.get("priority"), lang)

    overdue_badge = overdue_chip(lang) if ticket.get("overdue") else ""
    esc_lvl = ticket.get("escalation_level")
    escalation_badge = escalation_chip(int(esc_lvl), lang) if esc_lvl and int(esc_lvl) > 0 else ""

    dept_val = ticket.get("department", "General Administration")
    dept = esc(label("departments", dept_val, lang))
    cat_val = ticket.get("category", "General")
    cat = esc(label("categories", cat_val, lang))
    eng_note = esc(ui("english_note", lang))
    loc_val = ticket.get("location") or ticket.get("area")
    loc = esc(loc_val) if loc_val else '<span style="color: var(--muted); font-style: italic;">Protected</span>'
    due_by = esc(ticket.get("sla_due_at") or "N/A")

    summary_val = ticket.get("summary") or ticket.get("original_text")
    if summary_val:
        summary_html = f"""
        <div style="border-top: 1px solid var(--border); padding-top: 10px; margin-top: 8px;">
            <span class="understanding-label">{esc(ui('summary_title', lang))} <small style="font-weight:normal;opacity:0.8;">{eng_note}</small></span>
            <p style="margin: 4px 0 0 0; font-size: 14.5px; color: var(--text);">{esc(summary_val)}</p>
        </div>
        """
    else:
        summary_html = f"""
        <div style="border-top: 1px solid var(--border); padding-top: 10px; margin-top: 8px;">
            <span class="understanding-label">{esc(ui('summary_title', lang))}</span>
            <p style="margin: 4px 0 0 0; font-size: 13.5px; color: var(--muted); font-style: italic;">{esc(ui('details_locked_hint', lang))}</p>
        </div>
        """

    cluster_html = ""
    cluster_id = ticket.get("cluster_id")
    if cluster_id:
        cluster_info = ticket.get("cluster") or {}
        count = cluster_info.get("report_count", 2) if isinstance(cluster_info, dict) else 2
        cluster_html = f'<div class="small-note" style="color: var(--primary); font-weight: 500; margin-top: 6px;">{esc(ui("cluster_note", lang, count=count))}</div>'

    review_html = ""
    if ticket.get("needs_review"):
        review_html = f'<div class="small-note" style="color: var(--badge); font-weight: 500; margin-top: 4px;">{esc(ui("review_note", lang))}</div>'

    return f"""
    <div class="ticket-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
            <span class="id-chip">{tid}</span>
            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                {status_html}
                {p_chip}
                {overdue_badge}
                {escalation_badge}
            </div>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 12px;">
            <div>
                <span class="understanding-label">{esc(ui('department', lang))}</span>
                <div style="font-weight: 600; font-size: 15px;">{dept}</div>
            </div>
            <div>
                <span class="understanding-label">{esc(ui('category', lang))}</span>
                <div style="font-weight: 600; font-size: 15px;">{cat}</div>
            </div>
            <div>
                <span class="understanding-label">{esc(ui('location', lang))}</span>
                <div style="font-weight: 600; font-size: 15px;">{loc}</div>
            </div>
            <div>
                <span class="understanding-label">{esc(ui('due_by', lang))}</span>
                <div style="font-weight: 600; font-size: 15px;">{due_by}</div>
            </div>
        </div>
        {summary_html}
        {cluster_html}
        {review_html}
    </div>
    """

def build_receipt(ticket: Dict[str, Any], lang: str = "en", pin: Optional[str] = None) -> str:
    """Generates official plain-text grievance acknowledgement receipt, including PIN only when passed."""
    tid = ticket.get("ticket_id", "N/A")
    status = ticket.get("status", "Submitted")
    priority = ticket.get("priority", "Medium")
    dept = ticket.get("department", "General Administration")
    cat = ticket.get("category", "General")
    loc = ticket.get("location") or ticket.get("area") or "Not specified"
    created = ticket.get("created_at", "N/A")
    due_by = ticket.get("sla_due_at", "N/A")
    conf_val = ticket.get("confidence")
    conf = round(float(conf_val if conf_val is not None else 0.95) * 100)
    summary = ticket.get("summary") or ticket.get("english_text") or ticket.get("original_text", "")
    orig = ticket.get("original_text", "")

    lines = [
        "=" * 56,
        "              JANSAMADHAN GRIEVANCE RECEIPT             ",
        "=" * 56,
        f"Ticket ID:          {tid}",
    ]
    if pin:
        lines.append(f"Tracking PIN:       {pin}")
    lines.extend([
        f"Status:             {status}",
        f"Priority:           {priority}",
        f"Department:         {dept}",
        f"Category:           {cat}",
        f"Location / Ward:    {loc}",
        f"Registered At:      {created}",
        f"SLA Due By:         {due_by}",
        f"Classification:     {conf}% Confidence",
    ])
    if ticket.get("overdue"):
        lines.append(f"Overdue Notice:     YES")
    if ticket.get("escalation_level"):
        lines.append(f"Escalation Level:   Level {ticket.get('escalation_level')}")

    if summary:
        lines.extend([
            "-" * 56,
            "Summary:",
            f"{summary}",
        ])
    if orig:
        lines.extend([
            "-" * 56,
            "Original Complaint:",
            f"{orig}",
        ])
    lines.extend([
        "=" * 56,
        "Portal: JanSamadhan Multilingual Citizen AI Helpdesk",
        "=" * 56
    ])
    return "\n".join(lines)

def sidebar_brand() -> str:
    """Renders text wordmark, speech-bubble check icon, and tagline for sidebar header."""
    from icons import icon
    speech_icon = icon("speech_check", size=24, color="#FFFFFF")
    return f"""
    <div class="sidebar-brand-container" style="margin-bottom: 1.5rem; padding: 4px 6px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div class="brand-icon-pill" style="width: 38px; height: 38px; border-radius: 10px; background: rgba(255, 255, 255, 0.15); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                {speech_icon}
            </div>
            <div>
                <div style="font-size: 1.25rem; font-weight: 800; color: #FFFFFF; letter-spacing: -0.3px; line-height: 1.2;">JanSamadhan</div>
                <div style="font-size: 0.72rem; color: rgba(255, 255, 255, 0.85); font-weight: 500; margin-top: 2px; line-height: 1.2;">Citizen Grievance Redressal Platform</div>
            </div>
        </div>
    </div>
    """

