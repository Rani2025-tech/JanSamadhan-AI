import os
import json
from typing import Dict, Any, List, Optional

_LOCALES_CACHE: Dict[str, dict] = {}
_LANGUAGES_CACHE: Optional[List[dict]] = None

def _get_locales_dir() -> str:
    env_dir = os.environ.get("LOCALES_DIR")
    if env_dir and os.path.isdir(env_dir):
        return env_dir
    # Relative to this file: frontend/ui_text.py -> repo_root/locales
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidate = os.path.join(repo_root, "locales")
    if os.path.isdir(candidate):
        return candidate
    return os.path.join(os.getcwd(), "locales")

def _load_locale(lang: str) -> dict:
    code = (lang or "en").lower().strip()
    if code in _LOCALES_CACHE:
        return _LOCALES_CACHE[code]
    locales_dir = _get_locales_dir()
    filepath = os.path.join(locales_dir, f"{code}.json")
    if os.path.isfile(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                _LOCALES_CACHE[code] = data
                return data
        except Exception:
            pass
    _LOCALES_CACHE[code] = {}
    return {}

def supported_languages() -> List[dict]:
    """
    Returns the ordered list of language dicts from languages.json,
    including only those whose <code.json> file exists on disk.
    """
    global _LANGUAGES_CACHE
    if _LANGUAGES_CACHE is not None:
        return _LANGUAGES_CACHE

    locales_dir = _get_locales_dir()
    lang_file = os.path.join(locales_dir, "languages.json")
    languages = []
    if os.path.isfile(lang_file):
        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                languages = json.load(f)
        except Exception:
            languages = []

    result = []
    for lang in languages:
        code = lang.get("code")
        if code and os.path.isfile(os.path.join(locales_dir, f"{code}.json")):
            result.append(lang)

    _LANGUAGES_CACHE = result
    return result

class _SafeDict(dict):
    def __missing__(self, key):
        return f"{{{key}}}"

def ui(key: str, lang: str = "en", **kwargs: Any) -> str:
    """
    Translates a frontend UI string key into target language.
    Falls back per key to English, then to the key name itself.
    Never raises on missing file, missing key, or unknown language.
    Supports kwargs formatting.
    """
    if not key:
        return ""
    code = (lang or "en").lower().strip()
    data = _load_locale(code)
    template = data.get("ui", {}).get(key)
    if template is None:
        en_data = _load_locale("en")
        template = en_data.get("ui", {}).get(key, key)
    try:
        return template.format_map(_SafeDict(**kwargs))
    except Exception:
        return template

def _normalize_kind(kind: str) -> str:
    k = (kind or "").lower().strip()
    mapping = {
        "category": "categories",
        "categories": "categories",
        "department": "departments",
        "departments": "departments",
        "status": "statuses",
        "statuses": "statuses",
        "priority": "priorities",
        "priorities": "priorities"
    }
    return mapping.get(k, k)

def label(kind: str, name: str, lang: str = "en") -> str:
    """
    Returns the localized label for a category, department, status, or priority.
    Falls back to the English label or name if missing.
    """
    if not name:
        return ""
    norm_kind = _normalize_kind(kind)
    code = (lang or "en").lower().strip()
    data = _load_locale(code)
    val = data.get("labels", {}).get(norm_kind, {}).get(name)
    if val:
        return val
    en_data = _load_locale("en")
    en_val = en_data.get("labels", {}).get(norm_kind, {}).get(name)
    if en_val:
        return en_val
    return name
