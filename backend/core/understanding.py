import os
import json
from typing import Dict, Any, List, Optional
from backend.core.language import detect_language
from backend.core.messages import supported_languages
from backend.core.llm_wrapper import chat_json, LLMUnavailable

_CATEGORIES: Optional[List[str]] = None

def _get_categories() -> List[str]:
    global _CATEGORIES
    if _CATEGORIES is None:
        data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "departments.json")
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                deps = json.load(f)
                _CATEGORIES = [d["category"] for d in deps]
        except Exception:
            _CATEGORIES = [
                "Water Supply", "Electricity", "Roads & Potholes", "Sanitation & Garbage",
                "Drainage & Sewage", "Street Lighting", "Public Health", "Police & Public Safety",
                "Transport", "Municipal Services & Property", "Other / Needs Review"
            ]
    return _CATEGORIES

def understand(text: str, ui_lang: Optional[str] = None) -> Dict[str, Any]:
    """
    Parses a citizen complaint in any supported language or Romanized text.
    Returns:
      language, mixed, english_text, category, location, summary, missing, used_llm, needs_review.
    Uses zero-network fallback on LLMUnavailable.
    """
    cleaned_text = (text or "").strip()
    valid_categories = _get_categories()
    lang_info = detect_language(cleaned_text, ui_lang=ui_lang)

    supported = supported_languages()
    supported_codes = [l["code"] for l in supported]
    supported_names = [f"{l.get('name', l['code'])} ({l['code']})" for l in supported]
    supported_str = ", ".join(supported_names)
    allowed_lang_codes = supported_codes + ["other"]

    categories_list_str = ", ".join(valid_categories)
    system_prompt = (
        f"You are an Indian municipal civic complaint analyzer. The user input may be in any of the "
        f"supported languages ({supported_str}), in another Indian language, or Romanized.\n"
        f"For Devanagari input, you must decide between Hindi (hi) and Marathi (mr).\n"
        f"Categories: [{categories_list_str}].\n"
        f"Extract and return ONLY a JSON object with keys:\n"
        f"- \"language\": detected language code (one of {allowed_lang_codes})\n"
        f"- \"mixed\": boolean (true if Hinglish/mixed languages, false otherwise)\n"
        f"- \"english_text\": accurate translation or normalization into clear English\n"
        f"- \"category\": EXACT name from the category list above. If uncertain, use \"Other / Needs Review\"\n"
        f"- \"location\": specific street, ward, landmark, colony, or place mentioned (string, or null if none mentioned. DO NOT invent)\n"
        f"- \"summary\": concise English summary in 20 words or fewer\n"
        f"- \"missing\": list of strings for missing vital info (e.g. [\"location\"] if location is null)\n"
        f"- \"needs_review\": boolean (true if ambiguous or category is Other / Needs Review, false otherwise)"
    )

    try:
        raw_res = chat_json(prompt=cleaned_text, system=system_prompt)
        if not isinstance(raw_res, dict):
            raise ValueError("LLM did not return a valid dictionary")

        # Validate & Coerce
        category = raw_res.get("category", "").strip()
        needs_review = bool(raw_res.get("needs_review", False))

        if category not in valid_categories:
            category = "Other / Needs Review"
            needs_review = True
        elif category == "Other / Needs Review":
            needs_review = True

        location = raw_res.get("location")
        if location:
            location = str(location).strip()
            if location.lower() in ("null", "none", "n/a", ""):
                location = None

        missing = raw_res.get("missing", [])
        if not isinstance(missing, list):
            missing = [str(missing)] if missing else []
        if location is None and "location" not in missing:
            missing.append("location")

        summary = str(raw_res.get("summary", "")).strip()
        if not summary:
            eng_text = str(raw_res.get("english_text", cleaned_text))
            summary = " ".join(eng_text.split()[:20])

        llm_lang = str(raw_res.get("language", "")).lower().strip()
        if llm_lang in supported_codes:
            language = llm_lang
        else:
            language = lang_info["code"]

        mixed = bool(raw_res.get("mixed", lang_info["mixed"]))

        return {
            "language": language,
            "mixed": mixed,
            "english_text": str(raw_res.get("english_text", cleaned_text)),
            "category": category,
            "location": location,
            "summary": summary,
            "missing": missing,
            "used_llm": True,
            "needs_review": needs_review
        }

    except (LLMUnavailable, Exception):
        # Graceful fallback: zero LLM dependencies
        words = cleaned_text.split()
        summary_fallback = " ".join(words[:20]) if words else "Civic Complaint"
        return {
            "language": lang_info["code"],
            "mixed": lang_info["mixed"],
            "english_text": cleaned_text,
            "category": "Other / Needs Review",
            "location": None,
            "summary": summary_fallback,
            "missing": ["location"],
            "used_llm": False,
            "needs_review": True
        }
