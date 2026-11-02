import os
from typing import Dict, Any, Optional
from backend.core.llm_wrapper import chat, LLMUnavailable

def detect_script(text: str) -> str:
    """
    Detects script: 'odia', 'devanagari', 'bengali', 'tamil', 'telugu', 'latin', or 'mixed'.
    Majority wins, marked 'mixed' if both Indic and Latin characters are significant.
    """
    if not text:
        return "latin"

    odia_count = 0
    devanagari_count = 0
    bengali_count = 0
    tamil_count = 0
    telugu_count = 0
    latin_count = 0

    for ch in text:
        cp = ord(ch)
        if 0x0B00 <= cp <= 0x0B7F:
            odia_count += 1
        elif 0x0900 <= cp <= 0x097F:
            devanagari_count += 1
        elif 0x0980 <= cp <= 0x09FF:
            bengali_count += 1
        elif 0x0B80 <= cp <= 0x0BFF:
            tamil_count += 1
        elif 0x0C00 <= cp <= 0x0C7F:
            telugu_count += 1
        elif ('a' <= ch <= 'z') or ('A' <= ch <= 'Z'):
            latin_count += 1

    indic_count = odia_count + devanagari_count + bengali_count + tamil_count + telugu_count
    if indic_count >= 2 and latin_count >= 2:
        return "mixed"

    counts = {
        "odia": odia_count,
        "devanagari": devanagari_count,
        "bengali": bengali_count,
        "tamil": tamil_count,
        "telugu": telugu_count,
    }
    max_script, max_count = max(counts.items(), key=lambda x: x[1])

    if max_count > 0 and max_count >= latin_count:
        return max_script
    if latin_count > 0:
        return "latin"
    if max_count > 0:
        return max_script
    return "latin"

def detect_language(text: str, ui_lang: Optional[str] = None) -> Dict[str, Any]:
    """
    Detects language returning {'code': str, 'method': 'script'|'langdetect', 'mixed': bool}.
    Maps scripts:
      bengali -> bn
      tamil -> ta
      odia -> or
      devanagari -> ui_lang if ui_lang in ('mr', 'hi') else 'hi'
      telugu / unsupported script -> 'other'
    Latin script resolves via langdetect to 'en' or 'other'.
    Never crashes on empty text.
    """
    if not text or not text.strip():
        return {"code": "en", "method": "langdetect", "mixed": False}

    script = detect_script(text)

    try:
        from backend.core.messages import supported_languages
        supported = {l["code"] for l in supported_languages()}
    except Exception:
        supported = {"en", "hi", "mr", "ta", "bn", "or"}

    if script in ("odia", "devanagari", "bengali", "tamil", "telugu"):
        if script == "odia":
            code = "or"
        elif script == "bengali":
            code = "bn"
        elif script == "tamil":
            code = "ta"
        elif script == "devanagari":
            code = ui_lang if ui_lang in ("mr", "hi") else "hi"
        else:
            code = "other"

        if code not in supported:
            code = "other"
        return {"code": code, "method": "script", "mixed": False}

    if script == "mixed":
        counts = {
            "odia": sum(1 for c in text if 0x0B00 <= ord(c) <= 0x0B7F),
            "devanagari": sum(1 for c in text if 0x0900 <= ord(c) <= 0x097F),
            "bengali": sum(1 for c in text if 0x0980 <= ord(c) <= 0x09FF),
            "tamil": sum(1 for c in text if 0x0B80 <= ord(c) <= 0x0BFF),
            "telugu": sum(1 for c in text if 0x0C00 <= ord(c) <= 0x0C7F),
        }
        max_script, count = max(counts.items(), key=lambda x: x[1])
        if count == 0:
            code = "en"
        elif max_script == "odia":
            code = "or"
        elif max_script == "bengali":
            code = "bn"
        elif max_script == "tamil":
            code = "ta"
        elif max_script == "devanagari":
            code = ui_lang if ui_lang in ("mr", "hi") else "hi"
        else:
            code = "other"

        if code not in supported:
            code = "other"
        return {"code": code, "method": "script", "mixed": True}

    # Latin script
    try:
        from langdetect import detect
        detected = detect(text)
        code = "en" if detected == "en" else "other"
    except Exception:
        code = "en"
    return {"code": code, "method": "langdetect", "mixed": False}

def from_english(text: str, target_code: str) -> str:
    """
    Translate English reply into target language using llm_wrapper.chat.
    Returns text as-is if target is 'en' or upon LLMUnavailable.
    """
    if not text or target_code == "en":
        return text

    target_map = {
        "hi": "Hindi",
        "mr": "Marathi",
        "ta": "Tamil",
        "bn": "Bengali",
        "or": "Odia"
    }
    target_lang = target_map.get(target_code)
    if not target_lang:
        return text

    system = (
        f"You are a professional civic translator. Translate the given English text into clean, "
        f"accurate, courteous {target_lang}. Return ONLY the direct translation."
    )

    try:
        translated = chat(text, system=system, temperature=0.1, max_tokens=600)
        return translated.strip() if translated else text
    except LLMUnavailable:
        return text
    except Exception:
        return text
