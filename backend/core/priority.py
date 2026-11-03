import re
from typing import Dict, Any, List

SCORE_CRITICAL = 70
SCORE_HIGH = 40
SCORE_MEDIUM = 20

# English danger keywords triggering Critical
DANGER_KEYWORDS = [
    "live wire", "electric shock", "fire", "gas leak", "open manhole",
    "accident", "flood", "collapse", "sparking", "dead body"
]

# Vulnerable population / sensitive locations
VULNERABLE_KEYWORDS = [
    "child", "school", "hospital", "elderly", "patient", "pregnant", "clinic", "kindergarten"
]

# Category baseline weights
CATEGORY_WEIGHTS = {
    "Public Health": 25,
    "Police & Public Safety": 25,
    "Drainage & Sewage": 25,
    "Water Supply": 15,
    "Electricity": 15,
    "Roads & Potholes": 15,
    "Transport": 10,
    "Street Lighting": 5,
    "Sanitation & Garbage": 5,
    "Municipal Services & Property": 5,
    "Other / Needs Review": 5
}

# needs review by a fluent speaker
INDIC_DANGER_WORDS_HI = [
    "आग", "करंट", "बिजली का तार", "दुर्घटना", "बाढ़", "खुला नाला", "गैस लीक", "शव", "विस्फोट"
]

# needs review by a fluent speaker
INDIC_DANGER_WORDS_OR = [
    "ନିଆଁ", "କରେଣ୍ଟ", "ଦୁର୍ଘଟଣା", "ଖୋଲା ନାଳ", "ବନ୍ୟା", "ବିପଦ", "ଶବ", "ବିସ୍ଫୋରଣ"
]

DURATION_REGEX = re.compile(
    r"\b(?:since|for)\s+(?:\d+|several|few|two|three|four|five)\s+(?:days?|weeks?|months?)\b|"
    r"\b(?:no water|no electricity|without power|no power)\s+for\s+(?:days?|weeks?)\b|"
    r"\b(?:since a week|for a week|for 3 days|for days)\b",
    re.IGNORECASE
)

def score_priority(english_text: str, category: str, original_text: str = "") -> Dict[str, Any]:
    """
    Computes priority (Low, Medium, High, Critical) and transparent reason without LLM calls.
    Scans English text, categories, and Indic danger words on original text.
    """
    eng_lower = (english_text or "").lower()
    orig_text = original_text or ""
    score = 0
    reasons: List[str] = []

    # 1. Direct Danger Keywords (English)
    for kw in DANGER_KEYWORDS:
        if kw in eng_lower:
            score = max(score, 90)
            reasons.append(f"danger keyword '{kw}'")

    # 2. Indic danger keyword scan on original_text
    # needs review by a fluent speaker
    for h_word in INDIC_DANGER_WORDS_HI:
        if h_word in orig_text:
            score = max(score, 90)
            reasons.append(f"Hindi urgency keyword '{h_word}'")

    for o_word in INDIC_DANGER_WORDS_OR:
        if o_word in orig_text:
            score = max(score, 90)
            reasons.append(f"Odia urgency keyword '{o_word}'")

    # If critical danger identified directly, skip incremental modifiers
    if score >= SCORE_CRITICAL:
        return {
            "priority": "Critical",
            "score": score,
            "reason": "Critical: " + ", ".join(reasons)
        }

    # 3. Category base weight
    base_weight = CATEGORY_WEIGHTS.get(category, 10)
    score += base_weight
    reasons.append(f"category base weight for {category} (+{base_weight})")

    # 4. Vulnerable individuals or places
    matched_vulnerable = [v for v in VULNERABLE_KEYWORDS if v in eng_lower]
    if matched_vulnerable:
        score += 25
        reasons.append(f"vulnerable keyword '{matched_vulnerable[0]}' (+25)")

    # 5. Prolonged duration
    duration_match = DURATION_REGEX.search(eng_lower)
    if duration_match:
        score += 25
        reasons.append(f"prolonged duration '{duration_match.group(0)}' (+25)")

    # 6. Map score to priority level
    if score >= SCORE_CRITICAL:
        priority = "Critical"
    elif score >= SCORE_HIGH:
        priority = "High"
    elif score >= SCORE_MEDIUM:
        priority = "Medium"
    else:
        priority = "Low"

    return {
        "priority": priority,
        "score": score,
        "reason": f"{priority}: " + ", ".join(reasons)
    }
