import logging
from .gemini_client import gemini_client

logger = logging.getLogger(__name__)

LANGUAGE_PROMPT_MAP = {
    "or": "Odia (ଓଡ଼ିଆ)",
    "odia": "Odia (ଓଡ଼ିଆ)",
    "hi": "Hindi (हिन्दी)",
    "hindi": "Hindi (हिन्दी)",
    "bn": "Bengali (বাংলা)",
    "bengali": "Bengali (বাংলা)",
    "mr": "Marathi (मराठी)",
    "marathi": "Marathi (मराठी)",
    "ta": "Tamil (தமிழ்)",
    "tamil": "Tamil (தமிழ்)",
    "te": "Telugu (తెలుగు)",
    "telugu": "Telugu (తెలుగు)",
    "en": "English",
    "english": "English"
}

def translate(text: str, target_lang: str = "en") -> str:
    """Translates text into the requested target language."""
    if not text or not text.strip():
        return text

    target_desc = LANGUAGE_PROMPT_MAP.get(target_lang.lower(), target_lang)

    if gemini_client.is_available:
        try:
            prompt = f"Translate the following official government grievance notice or remark into {target_desc}. Return ONLY the direct translation:\n\n{text}"
            res = gemini_client.generate_content(prompt)
            if res and res.strip():
                return res.strip()
        except Exception as e:
            logger.warning(f"Gemini translation failed: {e}")

    # Fallback: return original text
    return text

